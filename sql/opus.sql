CREATE TABLE `aspirations` (
  `id` int NOT NULL AUTO_INCREMENT,
  `text` varchar(1000) NOT NULL,
  `tags` varchar(2048),
  PRIMARY KEY (`id`)
) ENGINE=InnoDB;

CREATE TABLE `users` (
  `id` int NOT NULL AUTO_INCREMENT,
  `chat_id` varchar(45) NOT NULL,
  `first_name` varchar(500) NOT NULL,
  `is_bot` tinyint(1) NOT NULL DEFAULT '0',
  `last_name` varchar(500) DEFAULT NULL,
  `language_code` varchar(45) COLLATE latin1_swedish_ci DEFAULT NULL COMMENT 'E.g.: ''pt-br'', ''en-us''',
  `phone_number` varchar(45) DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `users_un` (`chat_id`)
) ENGINE=InnoDB;

CREATE TABLE `user_services` (
	chat_id varchar(45) NOT NULL,
	service_type varchar(64) NOT NULL,
	CONSTRAINT user_services_pk PRIMARY KEY (chat_id,service_type)
) ENGINE=InnoDB;
