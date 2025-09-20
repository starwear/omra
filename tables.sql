-- Создание базы данных
CREATE DATABASE omrabase CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE omrabase;

-- Таблица с пользователями
CREATE TABLE `users` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `email` TEXT NOT NULL,
    `password` TEXT NOT NULL
);

-- Таблица с данными пользователей
CREATE TABLE `user_data` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `email` TEXT NOT NULL,
    `nickname` TEXT NOT NULL,
    `groups` TEXT NOT NULL,
    `contacts` TEXT NOT NULL
);