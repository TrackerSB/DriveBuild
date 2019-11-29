CREATE TABLE IF NOT EXISTS Users
(
    username TEXT NOT NULL PRIMARY KEY,
    password TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS Tests
(
    sid         SERIAL NOT NULL PRIMARY KEY,
    environment TEXT,
    criteria    TEXT,
    result      TEXT,
    status      TEXT,
    started     TIMESTAMP,
    finished    TIMESTAMP,
    username    TEXT REFERENCES users (username)
);

CREATE TABLE IF NOT EXISTS VerificationCycles
(
    sid      INT       NOT NULL REFERENCES tests (sid),
    vid      TEXT      NOT NULL,
    tick     INT       NOT NULL,
    data     BYTEA     NOT NULL,
    started  TIMESTAMP NOT NULL,
    finished TIMESTAMP NOT NULL,
    PRIMARY KEY (sid, vid, tick)
);

