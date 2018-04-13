CREATE DATABASE remindanuki;

CREATE TABLE `remindanuki`.`senders` (
  id INT NOT NULL AUTO_INCREMENT
  ,send_id VARCHAR(64) NOT NULL
  ,created_at DATETIME DEFAULT CURRENT_TIMESTAMP
  ,primary key(id)
  ,index(send_id)
);

CREATE TABLE `remindanuki`.`reminders` (
  id INT NOT NULL AUTO_INCREMENT
  ,sender_id INT NOT NULL
  ,text VARCHAR(256)
  ,remind_at DATETIME NOT NULL
  ,created_at DATETIME DEFAULT CURRENT_TIMESTAMP
  ,PRIMARY KEY(id)
  ,FOREIGN KEY(sender_id) REFERENCES senders(id)
);
