import json
import os

import torch
import torchvision
from PIL import Image, UnidentifiedImageError
from torchvision import transforms as T
from torchvision.models.detection.faster_rcnn import FastRCNNPredictor
from ultralytics import YOLO

from app.core.settings import settings
from app.core.exceptions import InvalidImageError

DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")


class DetectionService:
    """
    공고물 위치 탐지기(Faster R-CNN) + 텍스트 영역 탐지기(YOLOv11n) 조합 서비스.
    무거운 모델을 들고 있으므로 앱 시작 시(lifespan) 인스턴스 하나만 만들어 재사용하세요.
    """

    def __init__(self):
        print(f"[DetectionService] device: {DEVICE}")
        print("[DetectionService] 공고물 위치 탐지기 로드 중...")
        self.notice_detector_model = self._load_notice_detector_model()
        self.label_map = self._get_notice_detector_label_map()
        print(f"[DetectionService] 공고물 클래스: {self.label_map}")

        print("[DetectionService] 텍스트 영역 탐지기 로드 중...")
        self.text_region_detector_model = self._load_text_region_detector_model()

        self.transform = T.Compose([T.ToTensor()])
        print("[DetectionService] 준비 완료")

    @staticmethod
    def _load_notice_detector_model():
        if not os.path.exists(settings.notice_detector_weights):
            raise FileNotFoundError(f"공고물 위치 탐지기 가중치를 찾을 수 없습니다: {settings.notice_detector_weights}")
        model = torchvision.models.detection.fasterrcnn_resnet50_fpn(weights=None)
        in_features = model.roi_heads.box_predictor.cls_score.in_features
        model.roi_heads.box_predictor = FastRCNNPredictor(in_features, settings.notice_detector_num_classes)
        model.load_state_dict(torch.load(settings.notice_detector_weights, map_location=DEVICE))
        model.to(DEVICE)
        model.eval()
        return model

    @staticmethod
    def _load_text_region_detector_model():
        if not os.path.exists(settings.text_region_detector_weights):
            raise FileNotFoundError(f"텍스트 영역 탐지기 가중치를 찾을 수 없습니다: {settings.text_region_detector_weights}")
        return YOLO(settings.text_region_detector_weights)

    @staticmethod
    def _get_notice_detector_label_map():
        if settings.notice_detector_coco_ann and os.path.exists(settings.notice_detector_coco_ann):
            with open(settings.notice_detector_coco_ann, encoding="utf-8") as f:
                ann = json.load(f)
            cats = sorted(ann["categories"], key=lambda c: c["id"])
            return {i + 1: c["name"] for i, c in enumerate(cats)}
        return {1: "banner", 2: "card_news", 3: "poster"}

    @staticmethod
    def _crop_with_padding(img_pil, box, padding=None):
        padding = settings.crop_padding if padding is None else padding
        W, H = img_pil.size
        x1, y1, x2, y2 = box
        bw, bh = x2 - x1, y2 - y1
        x1 = max(0, x1 - bw * padding)
        y1 = max(0, y1 - bh * padding)
        x2 = min(W, x2 + bw * padding)
        y2 = min(H, y2 + bh * padding)
        return img_pil.crop((x1, y1, x2, y2)), (x1, y1, x2, y2)

    @staticmethod
    def _load_image_safely(image_path: str):
        """
        업로드된 파일을 이미지로 안전하게 엽니다.
        - 열 수 없는 파일(이미지가 아니거나 손상된 파일)은 InvalidImageError로 변환
        - 픽셀 수가 지나치게 큰 이미지는 비율을 유지하며 축소 (메모리/추론 시간 보호)
        """
        try:
            img_pil = Image.open(image_path)
            img_pil.load()  # 실제 픽셀 데이터까지 읽어서 손상 여부를 여기서 확인
            img_pil = img_pil.convert("RGB")
        except (UnidentifiedImageError, OSError, ValueError) as e:
            raise InvalidImageError(f"이미지를 열 수 없습니다: {e}") from e

        w, h = img_pil.size
        if w * h > settings.max_image_pixels:
            scale = (settings.max_image_pixels / (w * h)) ** 0.5
            new_size = (max(1, int(w * scale)), max(1, int(h * scale)))
            img_pil = img_pil.resize(new_size)

        return img_pil

    def detect_svc(self, image_path: str) -> dict:
        """
        이미지 한 장을 탐지 파이프라인에 통과시켜 결과 반환.

        Raises:
            InvalidImageError: 파일을 이미지로 열 수 없는 경우 (깨진 파일, 이미지가 아닌 파일 등)

        Returns:
            {
                "objects": [
                    {
                        "class": "card_news", "box": [...], "score": 0.99,
                        "regions": [
                            {"class": "title", "box": [...], "score": 0.9, "crop_image": PIL.Image},
                            ...
                        ]
                    }
                ]
            }
        """
        img_pil = self._load_image_safely(image_path)

        img_tensor = self.transform(img_pil).to(DEVICE)
        with torch.no_grad():
            preds = self.notice_detector_model([img_tensor])[0]

        objects = []

        for box, score, label in zip(preds["boxes"], preds["scores"], preds["labels"]):
            if score.item() < settings.notice_detector_conf:
                continue

            cls_name = self.label_map.get(int(label.item()), f"class_{label.item()}")
            x1, y1, x2, y2 = box.tolist()

            cropped_pil, (cx1, cy1, cx2, cy2) = self._crop_with_padding(img_pil, [x1, y1, x2, y2])

            text_region_preds = self.text_region_detector_model.predict(
                cropped_pil, imgsz=640,
                device=str(DEVICE).replace("cuda", "0").replace("cpu", "cpu"),
                conf=settings.text_region_detector_conf, verbose=False
            )[0]

            regions = []
            if text_region_preds.boxes is not None:
                for box2, score2, cls2 in zip(
                    text_region_preds.boxes.xyxy, text_region_preds.boxes.conf, text_region_preds.boxes.cls
                ):
                    rx1, ry1, rx2, ry2 = box2.tolist()
                    r_cls = text_region_preds.names[int(cls2.item())]
                    r_score = float(score2.item())

                    abs_box = [rx1 + cx1, ry1 + cy1, rx2 + cx1, ry2 + cy1]
                    region_img = img_pil.crop((abs_box[0], abs_box[1], abs_box[2], abs_box[3]))

                    regions.append({
                        "class": r_cls,
                        "box": abs_box,
                        "score": r_score,
                        "crop_image": region_img,
                    })

            objects.append({
                "class": cls_name,
                "box": [x1, y1, x2, y2],
                "score": score.item(),
                "regions": regions,
            })

        return {"objects": objects}