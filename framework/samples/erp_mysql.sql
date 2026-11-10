-- MySQL dump 10.13  Distrib 8.0.36, for Linux (x86_64)
--
-- Host: 127.0.0.1    Database: erp_demo
-- ------------------------------------------------------
-- Server version	8.0.36
--
-- FICTIONAL SAMPLE DATA. All companies, people, emails and card numbers are invented.
-- Card numbers are the public test numbers published by card networks.

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET NAMES utf8mb4 */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;

--
-- Table structure for table `companies`
--

DROP TABLE IF EXISTS `companies`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `companies` (
  `id` int NOT NULL AUTO_INCREMENT,
  `name` varchar(100) NOT NULL,
  `country` char(2) DEFAULT NULL,
  `created_at` datetime DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=4 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

LOCK TABLES `companies` WRITE;
/*!40000 ALTER TABLE `companies` DISABLE KEYS */;
INSERT INTO `companies` VALUES (1,'Alpine Test Traders','DE','2020-01-05 09:00:00'),(2,'Harbor Sample Foods','NL','2021-03-14 09:00:00'),(3,'Meadow Example Tools','PK','2022-06-30 09:00:00');
/*!40000 ALTER TABLE `companies` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `users`
--

DROP TABLE IF EXISTS `users`;
CREATE TABLE `users` (
  `id` int NOT NULL AUTO_INCREMENT,
  `company_id` int DEFAULT NULL,
  `username` varchar(60) NOT NULL,
  `email` varchar(120) DEFAULT NULL,
  `password` varchar(64) DEFAULT NULL,
  `is_admin` tinyint DEFAULT '0',
  `created_at` datetime DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=8 DEFAULT CHARSET=utf8mb4;

LOCK TABLES `users` WRITE;
INSERT INTO `users` VALUES
(1,1,'anna.demo','anna@example.com','Summer2024!',1,'2024-01-10 08:00:00'),
(2,1,'ben.demo','ben@example.com','letmein123',0,'2024-02-11 08:00:00'),
(3,2,'cara.demo','cara@example.org','Password1',0,'2024-02-12 08:00:00'),
(4,2,'dev.demo','dev@example.org','qwerty987',1,'2024-03-01 08:00:00'),
(5,3,'emma.demo','emma@example.net','Winter2023!',0,'2024-03-02 08:00:00'),
(6,3,'finn.demo','finn@example.net','hunter22',0,'2024-03-03 08:00:00'),
(7,3,'gina.demo','gina-at-example','abc12345',0,'2024-03-04 08:00:00');
UNLOCK TABLES;

--
-- Table structure for table `customers` (no primary key, kept from a legacy import)
--

DROP TABLE IF EXISTS `customers`;
CREATE TABLE `customers` (
  `customer_id` int NOT NULL,
  `company_id` int NOT NULL,
  `customer_code` varchar(20) NOT NULL,
  `name` varchar(100) DEFAULT NULL,
  `email` varchar(120) DEFAULT NULL,
  `phone` varchar(30) DEFAULT NULL,
  `tags` varchar(255) DEFAULT NULL,
  `credit_limit` float DEFAULT NULL,
  `created_at` datetime DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=latin1;

LOCK TABLES `customers` WRITE;
INSERT INTO `customers` VALUES
(1,1,'C-1001','Rhine Demo GmbH','orders@rhine.example.com','+49 30 5550100','wholesale,priority,eu',5000.5,'2023-05-01 10:00:00'),
(2,1,'C-1002','Bavaria Sample AG','buy@bavaria.example.com','+49 89 5550101','retail,eu',2500,'2023-05-02 10:00:00'),
(3,1,'C-1003','Saxony Fake KG','hello@saxony.example.com','+49 351 5550102','wholesale,eu',12000.25,'2023-05-03 10:00:00'),
(4,2,'C-2001','Polder Test BV','inkoop@polder.example.org','+31 20 5550103','horeca,nl',800,'2023-06-01 10:00:00'),
(4,2,'C-2001','Polder Test BV','inkoop@polder.example.org','+31 20 5550103','horeca,nl',800,'2023-06-01 10:00:00'),
(5,2,'C-2002','Canal Example NV','info@canal.example.org','+31 10 5550104','retail,nl',950,'2023-06-02 10:00:00'),
(6,3,'C-3001','Indus Demo Pvt','sales@indus.example.net','+92 21 5550105','export,priority',4100,'2023-07-01 10:00:00'),
(7,3,'C-3002','Karakoram Sample Ltd','accounts@karakoram.example.net','+92 51 5550106','export',4100,'2023-07-02 10:00:00'),
(8,3,'C-3002','Karakoram Sample Ltd (dup)','accounts2@karakoram.example.net','+92 51 5550107','export',4100,'2023-07-03 10:00:00');
INSERT INTO `customers` VALUES
(9,1,'C-4009','Extra Demo 9','contact9@example.com','+1 555 0109','wholesale,eu',1009,'2023-08-10 10:00:00'),
(10,2,'C-4010','Extra Demo 10','contact10@example.com','+1 555 0110','retail,priority',1010,'2023-08-11 10:00:00'),
(11,3,'C-4011','Extra Demo 11','contact11@example.com','+1 555 0111','export,nl',1011,'2023-08-12 10:00:00'),
(12,1,'C-4012','Extra Demo 12','contact12@example.com','+1 555 0112','wholesale,eu',1012,'2023-08-13 10:00:00'),
(13,2,'C-4013','Extra Demo 13','contact13@example.com','+1 555 0113','retail,priority',1013,'2023-08-14 10:00:00'),
(14,3,'C-4014','Extra Demo 14','contact14@example.com','+1 555 0114','export,nl',1014,'2023-08-15 10:00:00'),
(15,1,'C-4015','Extra Demo 15','contact15@example.com','+1 555 0115','wholesale,eu',1015,'2023-08-16 10:00:00'),
(16,2,'C-4016','Extra Demo 16','contact16@example.com','+1 555 0116','retail,priority',1016,'2023-08-17 10:00:00'),
(17,3,'C-4017','Extra Demo 17','contact17@example.com','+1 555 0117','export,nl',1017,'2023-08-18 10:00:00'),
(18,1,'C-4018','Extra Demo 18','contact18@example.com','+1 555 0118','wholesale,eu',1018,'2023-08-19 10:00:00'),
(19,2,'C-4019','Extra Demo 19','contact19@example.com','+1 555 0119','retail,priority',1019,'2023-08-20 10:00:00'),
(20,3,'C-4020','Extra Demo 20','contact20@example.com','+1 555 0120','export,nl',1020,'2023-08-21 10:00:00'),
(21,1,'C-4021','Extra Demo 21','contact21@example.com','+1 555 0121','wholesale,eu',1021,'2023-08-22 10:00:00'),
(22,2,'C-4022','Extra Demo 22','contact22@example.com','+1 555 0122','retail,priority',1022,'2023-08-23 10:00:00'),
(23,3,'C-4023','Extra Demo 23','contact23@example.com','+1 555 0123','export,nl',1023,'2023-08-24 10:00:00'),
(24,1,'C-4024','Extra Demo 24','contact24@example.com','+1 555 0124','wholesale,eu',1024,'2023-08-25 10:00:00'),
(25,2,'C-4025','Extra Demo 25','contact25@example.com','+1 555 0125','retail,priority',1025,'2023-08-26 10:00:00'),
(26,3,'C-4026','Extra Demo 26','contact26@example.com','+1 555 0126','export,nl',1026,'2023-08-27 10:00:00');
UNLOCK TABLES;

--
-- Table structure for table `products`
--

DROP TABLE IF EXISTS `products`;
CREATE TABLE `products` (
  `id` int NOT NULL AUTO_INCREMENT,
  `company_id` int NOT NULL,
  `sku` varchar(30) NOT NULL,
  `name` varchar(120) NOT NULL,
  `price` float NOT NULL,
  `cost` double DEFAULT NULL,
  `category_ids` varchar(100) DEFAULT NULL,
  `status` varchar(20) DEFAULT 'active',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=7 DEFAULT CHARSET=utf8mb4;

LOCK TABLES `products` WRITE;
INSERT INTO `products` VALUES
(1,1,'BOLT-01','Steel bolt M8',0.35,0.1,'3,7,9','active'),
(2,1,'NUT-01','Steel nut M8',0.2,0.07,'3,7','active'),
(3,2,'OIL-05','Olive oil 5l',41.9,28.15,'12,14','active'),
(4,2,'SALT-01','Sea salt 1kg',2.4,0.9,'12','active'),
(5,3,'DRILL-9','Cordless drill',120.0,88.4,'21,22,23','active'),
(6,3,'SAW-3','Hand saw',18.75,9.2,'21','discontinued');
INSERT INTO `products` VALUES
(7,2,'ITEM-07','Filler part 7',8.5,7.5,'12,14,16','active'),
(8,3,'ITEM-08','Filler part 8',9.5,8.5,'21,22','active'),
(9,1,'ITEM-09','Filler part 9',10.5,9.5,'3,7','active'),
(10,2,'ITEM-10','Filler part 10',11.5,10.5,'12,14,16','active'),
(11,3,'ITEM-11','Filler part 11',12.5,11.5,'21,22','active'),
(12,1,'ITEM-12','Filler part 12',13.5,12.5,'3,7','active'),
(13,2,'ITEM-13','Filler part 13',14.5,13.5,'12,14,16','active'),
(14,3,'ITEM-14','Filler part 14',15.5,14.5,'21,22','active'),
(15,1,'ITEM-15','Filler part 15',16.5,15.5,'3,7','active'),
(16,2,'ITEM-16','Filler part 16',17.5,16.5,'12,14,16','active'),
(17,3,'ITEM-17','Filler part 17',18.5,17.5,'21,22','active'),
(18,1,'ITEM-18','Filler part 18',19.5,18.5,'3,7','active'),
(19,2,'ITEM-19','Filler part 19',20.5,19.5,'12,14,16','active'),
(20,3,'ITEM-20','Filler part 20',21.5,20.5,'21,22','active'),
(21,1,'ITEM-21','Filler part 21',22.5,21.5,'3,7','active'),
(22,2,'ITEM-22','Filler part 22',23.5,22.5,'12,14,16','active'),
(23,3,'ITEM-23','Filler part 23',24.5,23.5,'21,22','active'),
(24,1,'ITEM-24','Filler part 24',25.5,24.5,'3,7','active'),
(25,2,'ITEM-25','Filler part 25',26.5,25.5,'12,14,16','active'),
(26,3,'ITEM-26','Filler part 26',27.5,26.5,'21,22','active');
UNLOCK TABLES;

--
-- Table structure for table `orders`
--

DROP TABLE IF EXISTS `orders`;
CREATE TABLE `orders` (
  `id` int NOT NULL AUTO_INCREMENT,
  `company_id` int NOT NULL,
  `customer_id` int DEFAULT NULL,
  `order_date` varchar(20) DEFAULT NULL,
  `total` float DEFAULT NULL,
  `status` varchar(20) DEFAULT NULL,
  `created_at` datetime DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=9 DEFAULT CHARSET=utf8mb4;

LOCK TABLES `orders` WRITE;
INSERT INTO `orders` VALUES
(1,1,1,'2025-01-15',350.5,'shipped','2025-01-15 11:00:00'),
(2,1,2,'2025-01-16',80,'shipped','2025-01-16 11:00:00'),
(3,1,3,'2025-02-01',1200.25,'open','2025-02-01 11:00:00'),
(4,2,4,'2025-02-03',419,'open','2025-02-03 11:00:00'),
(5,2,5,'2025-02-04',48,'cancelled','2025-02-04 11:00:00'),
(6,3,6,'2025-02-05',600,'open','2025-02-05 11:00:00'),
(7,3,99,'2025-02-06',37.5,'open','2025-02-06 11:00:00'),
(8,3,77,'2025-02-07',120,'open','2025-02-07 11:00:00');
INSERT INTO `orders` VALUES
(9,1,2,'2025-03-10',19,'open','2025-03-10 11:00:00'),
(10,2,3,'2025-03-11',20,'open','2025-03-11 11:00:00'),
(11,3,4,'2025-03-12',21,'open','2025-03-12 11:00:00'),
(12,1,5,'2025-03-13',22,'open','2025-03-13 11:00:00'),
(13,2,6,'2025-03-14',23,'open','2025-03-14 11:00:00'),
(14,3,7,'2025-03-15',24,'open','2025-03-15 11:00:00'),
(15,1,8,'2025-03-16',25,'open','2025-03-16 11:00:00'),
(16,2,1,'2025-03-17',26,'open','2025-03-17 11:00:00'),
(17,3,2,'2025-03-18',27,'open','2025-03-18 11:00:00'),
(18,1,3,'2025-03-19',28,'open','2025-03-19 11:00:00'),
(19,2,4,'2025-03-20',29,'open','2025-03-20 11:00:00'),
(20,3,5,'2025-03-21',30,'open','2025-03-21 11:00:00'),
(21,1,6,'2025-03-22',31,'open','2025-03-22 11:00:00'),
(22,2,7,'2025-03-23',32,'open','2025-03-23 11:00:00'),
(23,3,8,'2025-03-24',33,'open','2025-03-24 11:00:00'),
(24,1,1,'2025-03-25',34,'open','2025-03-25 11:00:00'),
(25,2,2,'2025-03-26',35,'open','2025-03-26 11:00:00'),
(26,3,3,'2025-03-27',36,'open','2025-03-27 11:00:00');
UNLOCK TABLES;

--
-- Table structure for table `order_items` (no primary key, no foreign keys)
--

DROP TABLE IF EXISTS `order_items`;
CREATE TABLE `order_items` (
  `order_id` int NOT NULL,
  `product_id` int NOT NULL,
  `quantity` int NOT NULL,
  `unit_price` float NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

LOCK TABLES `order_items` WRITE;
INSERT INTO `order_items` VALUES
(1,1,1000,0.35),(2,2,400,0.2),(3,1,3429,0.35),(4,3,10,41.9),(5,4,20,2.4),(6,5,5,120.0),
(55,4,3,2.4),(56,99,1,18.75),(6,6,4,18.75);
UNLOCK TABLES;

--
-- Table structure for table `accounts`
--

DROP TABLE IF EXISTS `accounts`;
CREATE TABLE `accounts` (
  `id` int NOT NULL AUTO_INCREMENT,
  `company_id` int NOT NULL,
  `code` varchar(10) NOT NULL,
  `name` varchar(80) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=5 DEFAULT CHARSET=utf8mb4;

LOCK TABLES `accounts` WRITE;
INSERT INTO `accounts` VALUES (1,1,'1000','Cash'),(2,1,'1200','Receivables'),(3,1,'4000','Sales'),(4,1,'2100','VAT payable');
UNLOCK TABLES;

--
-- Table structure for table `journal_entries`
--

DROP TABLE IF EXISTS `journal_entries`;
CREATE TABLE `journal_entries` (
  `id` int NOT NULL AUTO_INCREMENT,
  `company_id` int NOT NULL,
  `entry_number` varchar(20) NOT NULL,
  `entry_date` date NOT NULL,
  `description` varchar(200) DEFAULT NULL,
  `status` varchar(20) NOT NULL DEFAULT 'posted',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=5 DEFAULT CHARSET=utf8mb4;

LOCK TABLES `journal_entries` WRITE;
INSERT INTO `journal_entries` VALUES
(1,1,'JE-0001','2025-01-31','January sales','posted'),
(2,1,'JE-0002','2025-01-31','January VAT','posted'),
(3,1,'JE-0003','2025-02-28','February sales, unbalanced by a manual edit','posted'),
(4,1,'JE-0006','2025-03-31','March accruals','posted');
UNLOCK TABLES;

--
-- Table structure for table `journal_lines`
--

DROP TABLE IF EXISTS `journal_lines`;
CREATE TABLE `journal_lines` (
  `id` int NOT NULL AUTO_INCREMENT,
  `journal_entry_id` int NOT NULL,
  `account_id` int NOT NULL,
  `debit` float DEFAULT '0',
  `credit` float DEFAULT '0',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=9 DEFAULT CHARSET=utf8mb4;

LOCK TABLES `journal_lines` WRITE;
INSERT INTO `journal_lines` VALUES
(1,1,2,430.5,0),(2,1,3,0,430.5),
(3,2,3,76,0),(4,2,4,0,76),
(5,3,2,1200.25,0),(6,3,3,0,1100.25),
(7,4,1,50,0),(8,4,2,0,50);
UNLOCK TABLES;

--
-- Table structure for table `payments` (stores raw card data)
--

DROP TABLE IF EXISTS `payments`;
CREATE TABLE `payments` (
  `id` int NOT NULL AUTO_INCREMENT,
  `company_id` int NOT NULL,
  `order_id` int NOT NULL,
  `card_number` varchar(19) DEFAULT NULL,
  `cvv` varchar(4) DEFAULT NULL,
  `amount` float NOT NULL,
  `paid_at` datetime DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=6 DEFAULT CHARSET=utf8mb4;

LOCK TABLES `payments` WRITE;
INSERT INTO `payments` VALUES
(1,1,1,'4111111111111111','123',350.5,'2025-01-20 12:00:00'),
(2,1,2,'5555555555554444','456',80,'2025-01-21 12:00:00'),
(3,2,4,'378282246310005','7890',419,'2025-02-10 12:00:00'),
(4,3,6,'4012888888881881','321',300,'2025-02-11 12:00:00'),
(5,3,6,'6011111111111117','654',300,'2025-02-12 12:00:00');
UNLOCK TABLES;

--
-- Table structure for table `employees`
--

DROP TABLE IF EXISTS `employees`;
CREATE TABLE `employees` (
  `id` int NOT NULL AUTO_INCREMENT,
  `company_id` int NOT NULL,
  `full_name` varchar(100) NOT NULL,
  `national_id` varchar(30) DEFAULT NULL,
  `salary` float NOT NULL,
  `start_date` date DEFAULT NULL,
  `end_date` date DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=4 DEFAULT CHARSET=utf8mb4;

LOCK TABLES `employees` WRITE;
INSERT INTO `employees` VALUES
(1,1,'Lena Fictional','FAKE-000-001',4200.5,'2021-02-01',NULL),
(2,2,'Max Invented','FAKE-000-002',3900,'2022-05-01','2021-01-15'),
(3,3,'Sara Madeup','FAKE-000-003',2800,'2023-08-01',NULL);
UNLOCK TABLES;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;

-- Dump completed on 2025-03-31  8:00:00
