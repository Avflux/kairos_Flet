CREATE TABLE IF NOT EXISTS `users` (
	`id` int AUTO_INCREMENT NOT NULL,
	`nome` varchar(100) NOT NULL,
	`email` varchar(100) NOT NULL UNIQUE,
	`name_id` varchar(50) NOT NULL,
	`senha` varchar(255) NOT NULL,
	`data_entrada` date NOT NULL,
	`base_value` decimal(10,2) NOT NULL,
	`ociosidade` time NOT NULL,
	`is_logged_in` boolean NOT NULL DEFAULT false,
	`status` boolean NOT NULL DEFAULT true,
	`created_at` timestamp NOT NULL DEFAULT 'current_timestamp',
	`updated_at` timestamp NOT NULL DEFAULT 'current_timestamp',
	PRIMARY KEY (`id`)
);

CREATE TABLE IF NOT EXISTS `equipes` (
	`id` int AUTO_INCREMENT NOT NULL,
	`user_id` int NOT NULL,
	`nome` varchar(100) NOT NULL UNIQUE,
	`descricao` text NOT NULL,
	`created_at` timestamp NOT NULL DEFAULT 'current_timestamp',
	PRIMARY KEY (`id`)
);

CREATE TABLE IF NOT EXISTS `atividades` (
	`id` int AUTO_INCREMENT NOT NULL,
	`user_id` int NOT NULL,
	`description` text NOT NULL,
	`atividade` varchar(255) NOT NULL,
	`start_time` datetime NOT NULL,
	`end_time` datetime NOT NULL,
	`time_regress` time NOT NULL,
	`time_exceeded` time NOT NULL,
	`reason` varchar(255) NOT NULL,
	`total_time` time NOT NULL,
	`ativo` boolean NOT NULL DEFAULT true,
	`pausado` boolean NOT NULL DEFAULT false,
	`concluido` boolean NOT NULL DEFAULT false,
	`current_mode` varchar(20) NOT NULL,
	`created_at` timestamp NOT NULL DEFAULT 'current_timestamp',
	`updated_at` timestamp NOT NULL DEFAULT 'current_timestamp',
	PRIMARY KEY (`id`)
);

CREATE TABLE IF NOT EXISTS `user_lock_unlock` (
	`id` int AUTO_INCREMENT NOT NULL,
	`user_id` int NOT NULL,
	`lock_status` boolean NOT NULL DEFAULT false,
	`unlock_control` boolean NOT NULL DEFAULT true,
	`created_at` timestamp NOT NULL DEFAULT 'current_timestamp',
	`updated_at` timestamp NOT NULL DEFAULT 'current_timestamp',
	PRIMARY KEY (`id`)
);

CREATE TABLE IF NOT EXISTS `logs_sistema` (
	`id` int AUTO_INCREMENT NOT NULL,
	`user_id` int NOT NULL,
	`acao` varchar(100) NOT NULL,
	`descricao` text NOT NULL,
	`created_at` timestamp NOT NULL DEFAULT 'current_timestamp',
	PRIMARY KEY (`id`)
);

CREATE TABLE IF NOT EXISTS `system_config` (
	`id` int AUTO_INCREMENT NOT NULL,
	`config_key` varchar(50) NOT NULL UNIQUE,
	`config_value` text NOT NULL,
	`updated_at` timestamp NOT NULL DEFAULT 'current_timestamp',
	PRIMARY KEY (`id`)
);

CREATE TABLE IF NOT EXISTS `notification` (
	`id` int AUTO_INCREMENT NOT NULL,
	`user_id` int NOT NULL,
	`title` varchar(255) NOT NULL,
	`message` text NOT NULL,
	`category` varchar(50) NOT NULL DEFAULT 'general',
	`is_read` boolean NOT NULL DEFAULT false,
	`action_url` varchar(500) NOT NULL,
	`expires_at` timestamp NOT NULL,
	`created_at` timestamp NOT NULL DEFAULT 'current_timestamp',
	`updated_at` timestamp NOT NULL DEFAULT 'current_timestamp',
	PRIMARY KEY (`id`)
);

CREATE TABLE IF NOT EXISTS `notification_preferences` (
	`id` int AUTO_INCREMENT NOT NULL,
	`user_id` int NOT NULL,
	`notification_type` varchar(50) NOT NULL,
	`is_enabled` boolean NOT NULL DEFAULT true,
	`created_at` timestamp NOT NULL DEFAULT 'current_timestamp',
	`updated_at` timestamp NOT NULL DEFAULT 'current_timestamp',
	PRIMARY KEY (`id`)
);

CREATE TABLE IF NOT EXISTS `notification_deliveries` (
	`id` int AUTO_INCREMENT NOT NULL,
	`notification_id` int NOT NULL,
	`sent_at` timestamp NOT NULL,
	`delivered_at` timestamp NOT NULL,
	`error_message` text NOT NULL,
	`created_at` timestamp NOT NULL DEFAULT 'current_timestamp',
	PRIMARY KEY (`id`)
);

CREATE TABLE IF NOT EXISTS `projects` (
	`id` int AUTO_INCREMENT NOT NULL,
	`cliente` varchar(255) NOT NULL,
	`description` text NOT NULL,
	`numero` varchar(50) NOT NULL UNIQUE,
	`data_inicio` date NOT NULL,
	`data_final` date NOT NULL,
	`deadline` date NOT NULL,
	`budget` decimal(15,2) NOT NULL,
	`actual_cost` decimal(15,2) NOT NULL DEFAULT '0',
	`manager_id` int NOT NULL,
	`client_id` int NOT NULL,
	`progress` tinyint NOT NULL DEFAULT '0',
	`is_active` boolean NOT NULL DEFAULT true,
	`created_by` int NOT NULL,
	`created_at` timestamp NOT NULL DEFAULT 'current_timestamp',
	`updated_at` timestamp NOT NULL DEFAULT 'current_timestamp',
	PRIMARY KEY (`id`)
);

ALTER TABLE `equipes` ADD CONSTRAINT `equipes_fk1` FOREIGN KEY (`user_id`) REFERENCES `usuarios`(`id`);

ALTER TABLE `atividades` ADD CONSTRAINT `atividades_fk1` FOREIGN KEY (`user_id`) REFERENCES `usuarios`(`id`);
ALTER TABLE `user_lock_unlock` ADD CONSTRAINT `user_lock_unlock_fk1` FOREIGN KEY (`user_id`) REFERENCES `usuarios`(`id`);
ALTER TABLE `logs_sistema` ADD CONSTRAINT `logs_sistema_fk1` FOREIGN KEY (`user_id`) REFERENCES `usuarios`(`id`);

ALTER TABLE `notification` ADD CONSTRAINT `notification_fk1` FOREIGN KEY (`user_id`) REFERENCES `usuarios`(`id`);
ALTER TABLE `notification_preferences` ADD CONSTRAINT `notification_preferences_fk1` FOREIGN KEY (`user_id`) REFERENCES `usuarios`(`id`);
ALTER TABLE `notification_deliveries` ADD CONSTRAINT `notification_deliveries_fk1` FOREIGN KEY (`notification_id`) REFERENCES `notification`(`id`);
ALTER TABLE `projects` ADD CONSTRAINT `projects_fk9` FOREIGN KEY (`manager_id`) REFERENCES `users`(`id`);