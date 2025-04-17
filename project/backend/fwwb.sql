CREATE DATABASE  IF NOT EXISTS `fwwb` /*!40100 DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci */ /*!80016 DEFAULT ENCRYPTION='N' */;
USE `fwwb`;
-- MySQL dump 10.13  Distrib 8.0.41, for Win64 (x86_64)
--
-- Host: 127.0.0.1    Database: fwwb
-- ------------------------------------------------------
-- Server version	8.0.41

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!50503 SET NAMES utf8 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table `history`
--

DROP TABLE IF EXISTS `history`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `history` (
  `history_id` int NOT NULL AUTO_INCREMENT COMMENT '主键',
  `user_id` int NOT NULL COMMENT '外键',
  `video_id` varchar(512) NOT NULL,
  `create_time` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `status` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL COMMENT '状态值',
  `expiry` date DEFAULT NULL COMMENT '过期时间',
  PRIMARY KEY (`history_id`) USING BTREE,
  KEY `history__user` (`user_id`) USING BTREE,
  KEY `fk_history_video` (`video_id`),
  CONSTRAINT `fk_history_video` FOREIGN KEY (`video_id`) REFERENCES `user_videos` (`video_id`),
  CONSTRAINT `history__user` FOREIGN KEY (`user_id`) REFERENCES `users` (`user_id`) ON DELETE CASCADE ON UPDATE RESTRICT
) ENGINE=InnoDB AUTO_INCREMENT=53 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci ROW_FORMAT=DYNAMIC;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `history`
--

LOCK TABLES `history` WRITE;
/*!40000 ALTER TABLE `history` DISABLE KEYS */;
/*!40000 ALTER TABLE `history` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `user_videos`
--

DROP TABLE IF EXISTS `user_videos`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `user_videos` (
  `video_id` varchar(512) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL COMMENT '主键ID',
  `user_id` int NOT NULL COMMENT '用户ID，外键',
  `video_path` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL COMMENT '视频存储路径',
  PRIMARY KEY (`video_id` DESC) USING BTREE,
  KEY `fk_user_videos_user` (`user_id`) USING BTREE,
  CONSTRAINT `fk_user_videos_user` FOREIGN KEY (`user_id`) REFERENCES `users` (`user_id`) ON DELETE CASCADE ON UPDATE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci ROW_FORMAT=DYNAMIC;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `user_videos`
--

LOCK TABLES `user_videos` WRITE;
/*!40000 ALTER TABLE `user_videos` DISABLE KEYS */;
/*!40000 ALTER TABLE `user_videos` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `user_videos_process`
--

DROP TABLE IF EXISTS `user_videos_process`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `user_videos_process` (
  `video_id` varchar(512) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL COMMENT '主键ID',
  `user_id` int NOT NULL COMMENT '用户ID，外键',
  `video_path_process` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL COMMENT '视频存储路径',
  PRIMARY KEY (`video_id` DESC) USING BTREE,
  KEY `fk_user_videos_user_process` (`user_id`) USING BTREE,
  CONSTRAINT `fk_user_videos_user_process` FOREIGN KEY (`user_id`) REFERENCES `users` (`user_id`) ON DELETE CASCADE ON UPDATE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci ROW_FORMAT=DYNAMIC;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `user_videos_process`
--

LOCK TABLES `user_videos_process` WRITE;
/*!40000 ALTER TABLE `user_videos_process` DISABLE KEYS */;
/*!40000 ALTER TABLE `user_videos_process` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `users`
--

DROP TABLE IF EXISTS `users`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `users` (
  `user_id` int NOT NULL AUTO_INCREMENT COMMENT '自增长ID\r\n',
  `username` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL COMMENT '用户名',
  `phone` varchar(11) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL COMMENT '电话',
  `password_hash` varchar(128) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL COMMENT '哈希密码',
  `weixin` varchar(150) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL DEFAULT '' COMMENT '微信',
  `registration_date` timestamp(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6) COMMENT '注册时间',
  `role` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL DEFAULT 'member',
  PRIMARY KEY (`user_id`) USING BTREE,
  UNIQUE KEY `username` (`username`) USING BTREE,
  UNIQUE KEY `phone` (`phone`) USING BTREE,
  KEY `weixin` (`weixin`) USING BTREE
) ENGINE=InnoDB AUTO_INCREMENT=7 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci ROW_FORMAT=DYNAMIC;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `users`
--

LOCK TABLES `users` WRITE;
/*!40000 ALTER TABLE `users` DISABLE KEYS */;
INSERT INTO `users` VALUES (1,'测试账号','19100000003','pbkdf2:sha256:1000000$G9avP4gLoQTjxmNA$4a865708bd41c0655b87118f0066dab7ff2d5d56f064a09e3b259c37040abd27','','2025-03-12 11:44:46.125856','member'),(2,'空账号','19100000000','pbkdf2:sha256:1000000$5OQydItRmXJ7Iej8$58ead136848f7c0df3b91bbbf1b71101a0d1656d50e7136b8c4490b1938d613c','','2025-04-10 09:09:37.986364','member'),(3,'正式账号','18900000000','pbkdf2:sha256:1000000$Ehtwp4i4exV2bysj$546fd73b68075c1fbd6d1b797087c9ed07cddb3e00157302567ded6315c01600','','2025-03-26 11:44:58.712634','member');
/*!40000 ALTER TABLE `users` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `video_frames_pose`
--

DROP TABLE IF EXISTS `video_frames_pose`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `video_frames_pose` (
  `frame_id` varchar(512) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL COMMENT '主键ID',
  `video_id` varchar(512) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL COMMENT '视频ID\r\n视频ID，外键',
  `frame_index` int NOT NULL COMMENT '帧序号',
  `frame_path` varchar(512) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL COMMENT '帧图片路径',
  PRIMARY KEY (`frame_id`) USING BTREE,
  KEY `fk_frames_video` (`video_id`) USING BTREE,
  CONSTRAINT `fk_frames_video` FOREIGN KEY (`video_id`) REFERENCES `user_videos` (`video_id`) ON DELETE CASCADE ON UPDATE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci ROW_FORMAT=DYNAMIC;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `video_frames_pose`
--

LOCK TABLES `video_frames_pose` WRITE;
/*!40000 ALTER TABLE `video_frames_pose` DISABLE KEYS */;
/*!40000 ALTER TABLE `video_frames_pose` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `video_frames_process`
--

DROP TABLE IF EXISTS `video_frames_process`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `video_frames_process` (
  `frame_id` varchar(512) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL COMMENT '主键ID',
  `video_id` varchar(512) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL COMMENT '\r\n视频ID，外键',
  `frame_index` int NOT NULL COMMENT '帧序号',
  `frame_path_process` varchar(512) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL COMMENT '帧图片路径',
  PRIMARY KEY (`frame_id`) USING BTREE,
  KEY `fk_frames_video_process` (`video_id`) USING BTREE,
  CONSTRAINT `fk_frames_video_process` FOREIGN KEY (`video_id`) REFERENCES `user_videos` (`video_id`) ON DELETE CASCADE ON UPDATE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci ROW_FORMAT=DYNAMIC;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `video_frames_process`
--

LOCK TABLES `video_frames_process` WRITE;
/*!40000 ALTER TABLE `video_frames_process` DISABLE KEYS */;
/*!40000 ALTER TABLE `video_frames_process` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `video_status`
--

DROP TABLE IF EXISTS `video_status`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `video_status` (
  `video_id` varchar(512) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL COMMENT '视频ID,主键',
  `status` int NOT NULL COMMENT '状态',
  PRIMARY KEY (`video_id`) USING BTREE,
  CONSTRAINT `fk_video_status_video` FOREIGN KEY (`video_id`) REFERENCES `user_videos` (`video_id`) ON DELETE CASCADE ON UPDATE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci ROW_FORMAT=DYNAMIC;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `video_status`
--

LOCK TABLES `video_status` WRITE;
/*!40000 ALTER TABLE `video_status` DISABLE KEYS */;
/*!40000 ALTER TABLE `video_status` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Dumping routines for database 'fwwb'
--
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2025-04-17 16:15:26
