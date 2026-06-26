CREATE TABLE user (
    user_id           BIGINT      PRIMARY KEY AUTO_INCREMENT,
    name              VARCHAR(100),
    email             VARCHAR(100) UNIQUE,
    password          VARCHAR(255),
    role              VARCHAR(20)  DEFAULT 'USER',
    profile_completed BOOLEAN      DEFAULT FALSE,
    created_at        DATETIME     DEFAULT CURRENT_TIMESTAMP,
    updated_at        DATETIME     DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

CREATE TABLE user_profile (
    user_id                 BIGINT  PRIMARY KEY,
    age                     INT,
    gender                  VARCHAR(10),
    region                  VARCHAR(50),
    district                VARCHAR(50),
    education               VARCHAR(50),
    school_name             VARCHAR(100),
    major                   VARCHAR(100),
    student_status          VARCHAR(50),
    graduation_year         INT,
    employment_status       VARCHAR(50),
    occupation              VARCHAR(50),
    job_seeking             BOOLEAN  DEFAULT FALSE,
    career_history          TEXT,
    monthly_income          BIGINT,
    household_income_ratio  INT,
    household_size          INT,
    assets                  BIGINT,
    marital_status          VARCHAR(20),
    disability              BOOLEAN  DEFAULT FALSE,
    veteran                 BOOLEAN  DEFAULT FALSE,
    military_status         VARCHAR(20),
    startup_interest        BOOLEAN  DEFAULT FALSE,
    business_owner          BOOLEAN  DEFAULT FALSE,
    startup_status          VARCHAR(50),
    situation               TEXT,
    housing_status          VARCHAR(50),
    reason                  TEXT,
    updated_at              DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
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
    bizPrdEndYmd     VARCHAR(20),
    bizPrdEtcCn     VARCHAR(255),
    plcyAplyMthdCn  TEXT,
    aplyUrlAddr     VARCHAR(500),
    sbmsnDcmntCn    TEXT         NOT NULL,
    aplyYmd         VARCHAR(100) NOT NULL,
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
    addAplyQlfcCndCn TEXT         NOT NULL,
    ptcpPrpTrgtCn   TEXT         NOT NULL,
    mrgSttsCd       VARCHAR(20),
    inqCnt          INT          DEFAULT 0,
    frstRegDt       DATETIME,
    lastMdfcnDt     DATETIME,
    createdAt       DATETIME     DEFAULT CURRENT_TIMESTAMP,
    updatedAt       DATETIME     DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

CREATE INDEX idx_policy_age ON policy (sprtTrgtMinAge, sprtTrgtMaxAge);

CREATE TABLE policy_region (
    policy_id   BIGINT      NOT NULL,
    zip_code    VARCHAR(20) NOT NULL,
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
    result_id        BIGINT       PRIMARY KEY AUTO_INCREMENT,
    user_id          BIGINT       NOT NULL,
    policy_id        BIGINT       NOT NULL,
    simulation_input VARCHAR(500) NOT NULL,
    created_at       DATETIME     DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id)   REFERENCES user(user_id),
    FOREIGN KEY (policy_id) REFERENCES policy(policy_id)
);

CREATE TABLE ocr_result (
    ocr_id         BIGINT   PRIMARY KEY AUTO_INCREMENT,
    user_id        BIGINT   NOT NULL,
    extracted_text TEXT     NOT NULL,
    policy_id      BIGINT,
    created_at     DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id)   REFERENCES user(user_id),
    FOREIGN KEY (policy_id) REFERENCES policy(policy_id)
);

CREATE TABLE pdf_summary (
    pdf_id       BIGINT   PRIMARY KEY AUTO_INCREMENT,
    user_id      BIGINT   NOT NULL,
    summary_text TEXT     NOT NULL,
    policy_id    BIGINT,
    created_at   DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id)   REFERENCES user(user_id),
    FOREIGN KEY (policy_id) REFERENCES policy(policy_id)
);