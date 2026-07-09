CREATE TABLE code_master (
    code_group  VARCHAR(50)  NOT NULL,
    code_value  VARCHAR(50)  NOT NULL,
    code_label  VARCHAR(100) NOT NULL,
    sort_order  INT          DEFAULT 0,
    PRIMARY KEY (code_group, code_value)
);

INSERT INTO code_master VALUES
('GENDER',          'M',            '남성',     1),
('GENDER',          'F',            '여성',     2),
('EMPLOY',          'EMPLOYED',     '재직중',   1),
('EMPLOY',          'SEEKING',      '구직중',   2),
('EMPLOY',          'STUDENT',      '학생',     3),
('EMPLOY',          'FREELANCE',    '프리랜서', 4),
('EMPLOY',          'NONE',         '미취업',   5),
('MARITAL',         'SINGLE',       '미혼',     1),
('MARITAL',         'MARRIED',      '기혼',     2),
('MARITAL',         'DIVORCED',     '이혼',     3),
('EDUCATION',       'HIGH_SCHOOL',  '고졸',     1),
('EDUCATION',       'COLLEGE',      '대학재학', 2),
('EDUCATION',       'BACHELOR',     '대졸',     3),
('EDUCATION',       'MASTER',       '석사',     4),
('EDUCATION',       'DOCTOR',       '박사',     5),
('STUDENT_STATUS',  'ENROLLED',     '재학',     1),
('STUDENT_STATUS',  'LEAVE',        '휴학',     2),
('STUDENT_STATUS',  'GRADUATED',    '졸업',     3),
('STUDENT_STATUS',  'EXPECTED',     '졸업예정', 4),
('MILITARY',        'NONE',         '해당없음', 1),
('MILITARY',        'SERVING',      '복무중',   2),
('MILITARY',        'COMPLETED',    '전역',     3),
('MILITARY',        'EXEMPTED',     '면제',     4),
('STARTUP_STATUS',  'INTERESTED',   '관심있음', 1),
('STARTUP_STATUS',  'PREPARING',    '준비중',   2),
('STARTUP_STATUS',  'OPERATING',    '운영중',   3),
('HOUSING',         'OWN',          '자가',     1),
('HOUSING',         'RENT',         '전세',     2),
('HOUSING',         'MONTHLY',      '월세',     3),
('HOUSING',         'DORMITORY',    '기숙사',   4),
('HOUSING',         'ETC',          '기타',     5),
('NOTIFY_TYPE',     'BOOKMARK',     '즐겨찾기 정책 알림',   1),
('NOTIFY_TYPE',     'NEW_POLICY',   '새 정책 등록',         2),
('NOTIFY_TYPE',     'NOTICE',       '공지사항',             3),
('NOTIFY_TYPE',     'SYSTEM',       '시스템 알림',          4);

CREATE TABLE user (
    user_id           BIGINT       PRIMARY KEY AUTO_INCREMENT,
    name              VARCHAR(100),
    email             VARCHAR(100) UNIQUE,
    password          VARCHAR(255),
    role              VARCHAR(20)  DEFAULT 'USER',
    profile_completed BOOLEAN      DEFAULT FALSE,
    created_at        DATETIME     DEFAULT CURRENT_TIMESTAMP,
    updated_at        DATETIME     DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

CREATE TABLE email_verification (
    id          BIGINT       PRIMARY KEY AUTO_INCREMENT,
    email       VARCHAR(100) NOT NULL,
    code        VARCHAR(6)   NOT NULL,
    is_verified BOOLEAN      DEFAULT FALSE,
    expires_at  DATETIME     NOT NULL,
    created_at  DATETIME     DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE user_profile (
    user_id                BIGINT       PRIMARY KEY,
    birth_date             DATE,          -- age는 저장하지 않고 조회 시 계산
    gender                 VARCHAR(10),   -- AI rule engine 라벨값(남/여), code_master 아님
    region                 VARCHAR(50),
    district               VARCHAR(50),
    education              VARCHAR(50),
    school_name            VARCHAR(100),
    major                  VARCHAR(100),
    major_category         VARCHAR(50),   -- 전공계열, AI rule engine 라벨값(code_mapping.py MAJOR_MAP)
    student_status         VARCHAR(50),
    graduation_year        INT,
    employment_status      VARCHAR(50),   -- AI rule engine 라벨값(code_mapping.py JOB_MAP), code_master 아님
    occupation             VARCHAR(50),
    job_seeking            BOOLEAN      DEFAULT FALSE,
    career_history         TEXT,
    marital_status         VARCHAR(20),   -- AI rule engine 라벨값(code_mapping.py MARRIAGE_MAP), code_master 아님
    disability             BOOLEAN      DEFAULT FALSE,
    basic_livelihood       BOOLEAN      DEFAULT FALSE,  -- 기초생활수급자 여부
    single_parent          BOOLEAN      DEFAULT FALSE,  -- 한부모가정 여부
    startup_interest       BOOLEAN      DEFAULT FALSE,
    business_owner         BOOLEAN      DEFAULT FALSE,
    startup_status         VARCHAR(50),
    company_type           VARCHAR(50),
    situation              TEXT,
    housing_status         VARCHAR(50),
    reason                 TEXT,
    updated_at             DATETIME      DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES user(user_id)
);

CREATE TABLE policy (
    policy_id       BIGINT       PRIMARY KEY AUTO_INCREMENT,
    plcyNo          VARCHAR(50)  UNIQUE,
    plcyNm          VARCHAR(255) NOT NULL,
    plcyKywdNm      VARCHAR(255) NOT NULL,
    plcyExplnCn     TEXT         NOT NULL,
    lclsfNm         VARCHAR(100) NOT NULL,
    mclsfNm         VARCHAR(100) NOT NULL,
    plcySprtCn      TEXT         NOT NULL,
    sprvsnInstCdNm  VARCHAR(100),
    sprvsnInstPicNm VARCHAR(50),
    operInstCdNm    VARCHAR(100),
    operInstPicNm   VARCHAR(50),
    bizPrdBgngYmd   VARCHAR(20),
    bizPrdEndYmd    VARCHAR(20),
    bizPrdEtcCn     VARCHAR(255),
    plcyAplyMthdCn  TEXT,
    srngMthdCn      TEXT,
    aplyUrlAddr     VARCHAR(500),
    sbmsnDcmntCn    TEXT         NOT NULL,
    aplyYmd         VARCHAR(100) NOT NULL,
    aplyEndDt       DATE,        -- aplyYmd("YYYYMMDD ~ YYYYMMDD")에서 뽑아낸 마감일. 파싱 불가(상시 등)면 NULL
    refUrlAddr1     VARCHAR(500),
    refUrlAddr2     VARCHAR(500),
    etcMttrCn       TEXT,
    sprtSclCnt      INT,
    sprtTrgtMinAge  INT          NOT NULL,
    sprtTrgtMaxAge  INT          NOT NULL,
    earnMinAmt      BIGINT,
    earnMaxAmt      BIGINT,
    earnEtcCn       TEXT         NOT NULL,
    earnCndSeCd     VARCHAR(20),
    addAplyQlfcCndCn TEXT        NOT NULL,
    ptcpPrpTrgtCn   TEXT         NOT NULL,
    mrgSttsCd       VARCHAR(20),
    inqCnt          INT          DEFAULT 0,
    frstRegDt       DATETIME,
    lastMdfcnDt     DATETIME,
    createdAt       DATETIME     DEFAULT CURRENT_TIMESTAMP,
    updatedAt       DATETIME     DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

CREATE INDEX idx_policy_age ON policy (sprtTrgtMinAge, sprtTrgtMaxAge);

CREATE TABLE policy_schedule_event (
    event_id   BIGINT PRIMARY KEY AUTO_INCREMENT,
    policy_id  BIGINT      NOT NULL,
    event_type VARCHAR(20) NOT NULL,
    event_date VARCHAR(50) NOT NULL,
    raw_text   TEXT        NOT NULL,
    created_at DATETIME    DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (policy_id) REFERENCES policy(policy_id),
    UNIQUE (policy_id, event_type, event_date)
);

CREATE TABLE policy_ai_tip (
    policy_id    BIGINT PRIMARY KEY,
    tip          TEXT     NOT NULL,
    generated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (policy_id) REFERENCES policy(policy_id)
);

CREATE TABLE policy_region (
    policy_id BIGINT      NOT NULL,
    zip_code  VARCHAR(20) NOT NULL,
    PRIMARY KEY (policy_id, zip_code),
    FOREIGN KEY (policy_id) REFERENCES policy(policy_id)
);

CREATE TABLE bookmark (
    bookmark_id BIGINT   PRIMARY KEY AUTO_INCREMENT,
    user_id     BIGINT   NOT NULL,
    policy_id   BIGINT   NOT NULL,
    alarm_yn    BOOLEAN  DEFAULT FALSE,
    created_at  DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id)   REFERENCES user(user_id),
    FOREIGN KEY (policy_id) REFERENCES policy(policy_id),
    UNIQUE (user_id, policy_id)
);

CREATE TABLE notification (
    notification_id BIGINT       PRIMARY KEY AUTO_INCREMENT,
    user_id         BIGINT       NOT NULL,
    policy_id       BIGINT,
    notify_type     VARCHAR(20)  NOT NULL,
    title           VARCHAR(255) NOT NULL,
    content         TEXT,
    is_read         BOOLEAN      DEFAULT FALSE,
    created_at      DATETIME     DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id)   REFERENCES user(user_id),
    FOREIGN KEY (policy_id) REFERENCES policy(policy_id)
);

CREATE INDEX idx_notification_user ON notification (user_id, is_read);

CREATE TABLE inquiry (
    inquiry_id   BIGINT       PRIMARY KEY AUTO_INCREMENT,
    user_id      BIGINT,
    inquiry_type VARCHAR(50)  NOT NULL,
    title        VARCHAR(255) NOT NULL,
    content      TEXT         NOT NULL,
    answer       TEXT,
    status       VARCHAR(20)  DEFAULT 'PENDING',
    created_at   DATETIME     DEFAULT CURRENT_TIMESTAMP,
    answered_at  DATETIME,
    FOREIGN KEY (user_id) REFERENCES user(user_id)
);

CREATE TABLE ad_partnership_inquiry (
    ad_partnership_inquiry_id BIGINT       PRIMARY KEY AUTO_INCREMENT,
    user_id                   BIGINT,
    ad_name                   VARCHAR(255) NOT NULL,
    company_name              VARCHAR(255) NOT NULL,
    target_product            VARCHAR(255) NOT NULL,
    content                   TEXT         NOT NULL,
    answer                    TEXT,
    status                    VARCHAR(20)  DEFAULT 'PENDING',
    created_at                DATETIME     DEFAULT CURRENT_TIMESTAMP,
    answered_at               DATETIME,
    FOREIGN KEY (user_id) REFERENCES user(user_id)
);

CREATE TABLE corporate_support_inquiry (
    corporate_support_inquiry_id BIGINT       PRIMARY KEY AUTO_INCREMENT,
    user_id                      BIGINT,
    company_name                 VARCHAR(255) NOT NULL,
    support_content              TEXT         NOT NULL,
    support_period                VARCHAR(100) NOT NULL,

    answer                       TEXT,
    status                       VARCHAR(20)  DEFAULT 'PENDING',
    created_at                   DATETIME     DEFAULT CURRENT_TIMESTAMP,
    answered_at                  DATETIME,
    FOREIGN KEY (user_id) REFERENCES user(user_id)
);

CREATE TABLE notice (
    notice_id  BIGINT       PRIMARY KEY AUTO_INCREMENT,
    admin_id   BIGINT       NOT NULL,
    title      VARCHAR(255) NOT NULL,
    content    TEXT         NOT NULL,
    is_pinned  BOOLEAN      DEFAULT FALSE,
    created_at DATETIME     DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME     DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (admin_id) REFERENCES user(user_id)
);

CREATE TABLE simulation_result (
    result_id        BIGINT   PRIMARY KEY AUTO_INCREMENT,
    user_id          BIGINT   NOT NULL,
    policy_id        BIGINT   NOT NULL,
    simulation_input JSON     NOT NULL,
    created_at       DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id)   REFERENCES user(user_id),
    FOREIGN KEY (policy_id) REFERENCES policy(policy_id)
);

CREATE TABLE ocr_result (
    ocr_id         BIGINT   PRIMARY KEY AUTO_INCREMENT,
    user_id        BIGINT   NOT NULL,
    extracted_text TEXT     NOT NULL,
    created_at     DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES user(user_id)
);

CREATE TABLE ocr_result_match (
    ocr_id      BIGINT NOT NULL,
    policy_id   BIGINT NOT NULL,
    match_score FLOAT,
    match_type  VARCHAR(20),
    PRIMARY KEY (ocr_id, policy_id),
    FOREIGN KEY (ocr_id)    REFERENCES ocr_result(ocr_id),
    FOREIGN KEY (policy_id) REFERENCES policy(policy_id)
);

CREATE TABLE pdf_summary (
    pdf_id       BIGINT   PRIMARY KEY AUTO_INCREMENT,
    user_id      BIGINT   NOT NULL,
    summary_text TEXT     NOT NULL,
    created_at   DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES user(user_id)
);

CREATE TABLE pdf_summary_match (
    pdf_id      BIGINT NOT NULL,
    policy_id   BIGINT NOT NULL,
    match_score FLOAT,
    match_type  VARCHAR(20),
    PRIMARY KEY (pdf_id, policy_id),
    FOREIGN KEY (pdf_id)    REFERENCES pdf_summary(pdf_id),
    FOREIGN KEY (policy_id) REFERENCES policy(policy_id)
);