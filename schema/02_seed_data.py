# Databricks notebook source
# /// script
# [tool.databricks.environment]
# environment_version = "5"
# ///
# MAGIC %md
# MAGIC # 02 — Seed Data (Atlas Commercial Insurance Reference Implementation)
# MAGIC
# MAGIC Populates all 8 operational tables with realistic commercial trucking
# MAGIC insurance demo data. Run 01_create_tables first.

# COMMAND ----------

# DBTITLE 1,Setup sys.path
import sys, os

_nb_path   = dbutils.notebook.entry_point.getDbutils().notebook().getContext().notebookPath().get()
_repo_root = "/Workspace/" + "/".join(_nb_path.strip("/").split("/")[:-2])
_src_path  = os.path.join(_repo_root, "src")
if _src_path not in sys.path:
    sys.path.insert(0, _src_path)

# COMMAND ----------

# DBTITLE 1,Skip restart
# Python restart not needed — sys.path set above.

# COMMAND ----------

from uw_copilot.config import Config
cfg = Config()
C   = cfg.catalog
S   = cfg.schema
for t in ["insureds","policies","drivers","vehicles","claims","submissions","loss_runs","underwriting_referrals"]:
    spark.sql(f"DELETE FROM {C}.{S}.{t}")
print(f"Seeding {C}.{S} ...")

# COMMAND ----------

# MAGIC %md ## Insureds (12)

# COMMAND ----------

# DBTITLE 1,Cell 6
spark.sql(f"""INSERT INTO {C}.{S}.insureds VALUES ('INS-1001','Heartland Express Logistics','Heartland Express','1234567','MC-432156','IL','Springfield',18,85,102,'Regional','General Freight','Satisfactory',22.4,31.1,18.7,12.3,28500000.00,8925000,'Samsara',92.00,'Preferred','Sarah Mitchell','2019-03-15'),
('INS-1002','Pacific Coast Carriers Inc','PCC','2345678','MC-567890','CA','Fontana',12,42,48,'Long Haul','Refrigerated','Satisfactory',38.2,45.6,28.3,15.1,15200000.00,5460000,'KeepTruckin',78.00,'Acceptable','James Rodriguez','2020-07-01'),
('INS-1003','Summit Petroleum Transport LLC',NULL,'3456789','MC-678901','TX','Houston',22,35,40,'Regional','Petroleum/Chemicals','Satisfactory',15.8,22.4,20.1,8.9,42000000.00,3850000,'Omnitracs',100.00,'Preferred','Sarah Mitchell','2017-11-20'),
('INS-1004','Great Lakes Intermodal Corp','GLI','4567890','MC-789012','OH','Columbus',8,120,135,'Intermodal','Containers','Satisfactory',28.9,35.2,42.1,19.8,52000000.00,12600000,'Samsara',85.00,'Acceptable','David Chen','2021-01-10'),
('INS-1005','Lone Star Hauling Partners',NULL,'5678901','MC-890123','TX','Dallas',5,18,20,'Local','Construction Materials','Satisfactory',42.7,55.3,38.9,25.4,4800000.00,1260000,NULL,45.00,'Borderline','James Rodriguez','2023-04-01'),
('INS-1006','Mountain West Freight Systems','MW Freight','6789012','MC-901234','CO','Denver',15,65,72,'Regional','General Freight','Satisfactory',19.3,28.7,15.2,11.6,22800000.00,7150000,'Samsara',88.00,'Preferred','David Chen','2018-06-15'),
('INS-1007','Eastern Seaboard Logistics LLC','ESL','7890123','MC-012345','NJ','Newark',10,55,60,'Regional','General Freight','Conditional',52.1,48.9,55.3,32.7,18500000.00,5720000,'KeepTruckin',65.00,'Borderline','Sarah Mitchell','2022-09-01'),
('INS-1008','Cascade Timber Transport',NULL,'8901234','MC-123456','OR','Portland',20,28,30,'Local','Lumber/Forest Products','Satisfactory',25.6,18.9,22.4,14.2,9200000.00,2100000,'Samsara',95.00,'Preferred','David Chen','2016-02-28'),
('INS-1009','Gulf States Auto Carriers','GSAC','9012345','MC-234567','AL','Mobile',7,32,36,'Long Haul','Automobiles','Satisfactory',33.4,40.2,35.8,20.1,12400000.00,4680000,'Omnitracs',72.00,'Acceptable','James Rodriguez','2021-08-15'),
('INS-1010','Tri-State Tanker Corp',NULL,'1123456','MC-345678','PA','Allentown',25,22,24,'Intermediate','Fuel/Petroleum','Satisfactory',12.1,15.8,10.4,7.2,18900000.00,2860000,'Omnitracs',100.00,'Preferred','Sarah Mitchell','2015-05-10'),
('INS-1011','Midwest Flatbed Solutions','MFS','1234560','MC-456789','IN','Indianapolis',6,40,44,'Regional','Steel/Metals','Satisfactory',30.2,36.8,28.9,18.5,14500000.00,4160000,'Samsara',80.00,'Acceptable','David Chen','2022-03-01'),
('INS-1012','Sunbelt Dedicated Services','Sunbelt','2345670','MC-567801','GA','Atlanta',4,95,110,'Dedicated','Retail/Consumer','Satisfactory',20.8,25.3,19.7,13.4,38000000.00,9750000,'Samsara',90.00,'Preferred','James Rodriguez','2020-01-15'),
('INS-1013','Ironhorse Freight Systems LLC','Ironhorse Freight','3720145','MC-977321','IN','Indianapolis',9,8,8,'Regional','General Freight','Satisfactory',48.0,41.0,33.0,20.0,3400000.00,1120000,'Samsara',80.00,'Acceptable','David Chen','2026-06-25'),
('INS-1014','Dixie Express Lines','Dixie Express','5140231','MC-514023','TN','Nashville',14,52,58,'Long Haul','General Freight','Satisfactory',35.2,29.8,24.6,16.1,24500000.00,9200000,'Samsara',82.00,'Acceptable','James Rodriguez','2012-05-01')""")
print("  insureds: 14")

# COMMAND ----------

# MAGIC %md ## Policies (15)

# COMMAND ----------

# DBTITLE 1,Cell 8
spark.sql(f"""INSERT INTO {C}.{S}.policies VALUES ('ACI-AL-25-732053','INS-1001','Auto Liability','Active','2025-03-15','2026-03-15',425000.00,'1,000,000 CSL','2,000,000',5000.00,85,'IL','Midwest Transport Advisors','Sarah Mitchell','Auto-Renew',32.50),
('ACI-PD-25-732054','INS-1001','Physical Damage','Active','2025-03-15','2026-03-15',185000.00,'ACV',NULL,2500.00,85,'IL','Midwest Transport Advisors','Sarah Mitchell','Auto-Renew',28.10),
('ACI-MC-25-732055','INS-1001','Motor Truck Cargo','Active','2025-03-15','2026-03-15',42000.00,'250,000','500,000',1000.00,85,'IL','Midwest Transport Advisors','Sarah Mitchell','Auto-Renew',15.20),
('ACI-AL-25-845210','INS-1002','Auto Liability','Active','2025-07-01','2026-07-01',298000.00,'1,000,000 CSL','2,000,000',10000.00,42,'CA','Golden State Insurance Partners','James Rodriguez','Review Required',55.80),
('ACI-PD-25-845211','INS-1002','Physical Damage','Active','2025-07-01','2026-07-01',112000.00,'ACV',NULL,5000.00,42,'CA','Golden State Insurance Partners','James Rodriguez','Review Required',42.30),
('ACI-AL-25-690117','INS-1003','Auto Liability','Active','2025-11-20','2026-11-20',520000.00,'2,000,000 CSL','5,000,000',10000.00,35,'TX','Energy Risk Brokers','Sarah Mitchell','Auto-Renew',22.40),
('ACI-MC-25-690118','INS-1003','Motor Truck Cargo','Active','2025-11-20','2026-11-20',95000.00,'1,000,000','2,000,000',5000.00,35,'TX','Energy Risk Brokers','Sarah Mitchell','Auto-Renew',18.60),
('ACI-AL-26-901445','INS-1004','Auto Liability','Active','2026-01-10','2027-01-10',680000.00,'1,000,000 CSL','2,000,000',5000.00,120,'OH','National Fleet Insurance Group','David Chen','Auto-Renew',38.90),
('ACI-AL-25-553872','INS-1005','Auto Liability','Active','2025-04-01','2026-04-01',78000.00,'1,000,000 CSL','1,000,000',10000.00,18,'TX','Southwest Commercial Brokerage','James Rodriguez','Review Required',72.40),
('ACI-AL-25-618934','INS-1006','Auto Liability','Active','2025-06-15','2026-06-15',345000.00,'1,000,000 CSL','2,000,000',5000.00,65,'CO','Rocky Mountain Risk Partners','David Chen','Auto-Renew',28.70),
('ACI-UMB-25-618935','INS-1006','Umbrella','Active','2025-06-15','2026-06-15',85000.00,'5,000,000','5,000,000',0.00,65,'CO','Rocky Mountain Risk Partners','David Chen','Auto-Renew',12.30),
('ACI-AL-25-778321','INS-1007','Auto Liability','Active','2025-09-01','2026-09-01',310000.00,'1,000,000 CSL','1,000,000',15000.00,55,'NJ','Atlantic Specialty Brokers','Sarah Mitchell','Non-Renew',85.20),
('ACI-AL-24-732050','INS-1001','Auto Liability','Expired','2024-03-15','2025-03-15',398000.00,'1,000,000 CSL','2,000,000',5000.00,80,'IL','Midwest Transport Advisors','Sarah Mitchell','Auto-Renew',35.80),
('ACI-AL-24-845207','INS-1002','Auto Liability','Expired','2024-07-01','2025-07-01',275000.00,'1,000,000 CSL','2,000,000',10000.00,38,'CA','Golden State Insurance Partners','James Rodriguez','Auto-Renew',48.90),
('ACI-AL-23-732047','INS-1001','Auto Liability','Expired','2023-03-15','2024-03-15',372000.00,'1,000,000 CSL','2,000,000',5000.00,75,'IL','Midwest Transport Advisors','Sarah Mitchell','Auto-Renew',29.10)""")
print("  policies: 15")

# COMMAND ----------

# MAGIC %md ## Drivers (29)

# COMMAND ----------

# DBTITLE 1,Cell 10
spark.sql(f"""INSERT INTO {C}.{S}.drivers VALUES ('DRV-2001','INS-1001','Robert','Thompson','IL-CDL-88432156','IL','A','1978-05-12','2019-06-01',18,0,'2026-01-15','Active',false,false,false,0,0,92.4),
('DRV-2002','INS-1001','Maria','Gonzalez','IL-CDL-77321045','IL','A','1985-11-23','2020-02-15',12,1,'2026-01-15','Active',false,false,false,0,1,87.8),
('DRV-2003','INS-1001','James','Williams','MO-CDL-99654321','MO','A','1972-08-30','2019-03-20',24,0,'2026-01-15','Active',false,true,false,0,0,95.1),
('DRV-2004','INS-1001','David','Brown','IL-CDL-55789432','IL','A','1990-03-17','2022-08-10',7,2,'2026-01-15','Active',false,false,false,1,2,78.3),
('DRV-2005','INS-1001','Patricia','Davis','IN-CDL-44876543','IN','A','1982-12-05','2021-01-05',15,0,'2026-01-15','Active',false,false,true,0,0,91.7),
('DRV-2010','INS-1002','Michael','Chen','CA-CDL-33987654','CA','A','1980-07-22','2020-08-01',16,1,'2025-12-20','Active',false,false,false,0,1,84.2),
('DRV-2011','INS-1002','Carlos','Ramirez','CA-CDL-22109876','CA','A','1988-04-15','2021-03-15',9,3,'2025-12-20','Active',false,false,false,1,3,68.5),
('DRV-2012','INS-1002','Kevin','OBrien','AZ-CDL-11234567','AZ','A','1975-09-08','2020-07-15',22,0,'2025-12-20','Active',false,true,true,0,0,93.8),
('DRV-2013','INS-1002','Thomas','Jackson','CA-CDL-66543210','CA','A','1992-01-30','2023-11-01',4,5,'2025-12-20','Active',false,false,false,2,4,55.2),
('DRV-2014','INS-1002','Anthony','Morales','NV-CDL-88765432','NV','A','1983-06-19','2022-05-01',14,7,'2025-12-20','Excluded',true,false,false,1,2,42.0),
('DRV-2020','INS-1003','William','Harris','TX-CDL-77890123','TX','A','1970-02-14','2017-12-01',28,0,'2026-02-10','Active',false,true,true,0,0,97.2),
('DRV-2021','INS-1003','Richard','Martinez','TX-CDL-55012345','TX','A','1976-10-28','2018-06-15',22,0,'2026-02-10','Active',false,true,true,0,0,94.6),
('DRV-2022','INS-1003','Steven','Taylor','TX-CDL-33234567','TX','A','1984-07-03','2020-01-10',13,1,'2026-02-10','Active',false,true,false,0,1,88.9),
('DRV-2030','INS-1005','Randy','Foster','TX-CDL-11456789','TX','B','1987-11-15','2023-05-01',5,4,'2025-10-05','Active',false,false,false,2,3,58.4),
('DRV-2031','INS-1005','Mark','Powell','TX-CDL-99678901','TX','A','1991-03-22','2024-01-15',3,6,'2025-10-05','Active',false,false,false,1,5,45.1),
('DRV-2032','INS-1005','Daniel','Ward','TX-CDL-77890234','TX','A','1969-08-10','2023-04-01',30,2,'2025-10-05','Active',false,false,false,0,2,72.6),
('DRV-2040','INS-1007','Brian','Sullivan','NJ-CDL-55901234','NJ','A','1979-04-18','2022-10-01',17,3,'2025-11-15','Active',false,false,false,1,3,65.8),
('DRV-2041','INS-1007','Jose','Hernandez','NY-CDL-33012345','NY','A','1986-09-25','2023-02-01',10,4,'2025-11-15','Active',false,false,false,2,3,59.3),
('DRV-2042','INS-1007','Gregory','Bennett','NJ-CDL-11123456','NJ','A','1993-12-08','2024-06-01',3,7,'2025-11-15','Excluded',true,false,false,0,1,38.0),
('DRV-2050','INS-1006','Christopher','Anderson','CO-CDL-99234567','CO','A','1977-06-30','2018-07-01',20,0,'2026-03-01','Active',false,false,false,0,0,96.5),
('DRV-2051','INS-1006','Andrew','Nelson','CO-CDL-77345678','CO','A','1981-01-12','2019-04-15',16,0,'2026-03-01','Active',false,false,false,0,0,94.1),
('DRV-2052','INS-1006','Jennifer','Wright','WY-CDL-55456789','WY','A','1989-08-20','2021-11-01',8,1,'2026-03-01','Active',false,false,false,0,1,86.7),
('DRV-2060','INS-1004','Timothy','Clark','OH-CDL-33567890','OH','A','1974-03-05','2021-02-01',25,0,'2026-01-20','Active',false,false,false,0,0,93.4),
('DRV-2061','INS-1004','Ronald','Lewis','MI-CDL-11678901','MI','A','1986-10-17','2021-05-15',11,2,'2026-01-20','Active',false,false,false,1,2,76.8),
('DRV-2062','INS-1004','Laura','Robinson','OH-CDL-99789012','OH','A','1983-05-28','2022-01-10',14,1,'2026-01-20','Active',false,false,false,0,1,85.9),
('DRV-2070','INS-1012','Michelle','Walker','GA-CDL-77890123','GA','A','1980-12-03','2020-02-01',17,0,'2026-02-28','Active',false,false,false,0,0,94.8),
('DRV-2071','INS-1012','Jason','Hall','GA-CDL-55901234','GA','A','1988-07-14','2020-06-15',10,1,'2026-02-28','Active',false,false,false,0,1,88.2),
('DRV-2072','INS-1012','Stephanie','Young','FL-CDL-33012345','FL','A','1991-02-22','2022-09-01',7,0,'2026-02-28','Active',false,false,false,0,0,90.5),
('DRV-2099','INS-1005','Travis','Murphy','TX-CDL-11234590','TX','A','1985-05-05','2023-04-01',8,7,'2025-06-01','Terminated',true,false,false,1,2,30.0),
('DRV-2100','INS-1013','Gerald','Whitfield','IN-CDL-45120087','IN','A','1979-04-11','2018-05-01',16,0,'2026-05-01','Active',false,false,false,0,0,93.2),
('DRV-2101','INS-1013','Renee','Kowalski','IN-CDL-45120088','IN','A','1986-09-02','2019-03-15',12,1,'2026-05-01','Active',false,false,false,0,1,88.6),
('DRV-2102','INS-1013','Marcus','Delaney','IL-CDL-33120089','IL','A','1974-12-19','2017-08-10',22,0,'2026-05-01','Active',false,true,false,0,0,95.4),
('DRV-2103','INS-1013','Sophia','Reyes','OH-CDL-77120090','OH','A','1990-06-27','2021-02-01',8,2,'2026-05-01','Active',false,false,false,0,2,82.1),
('DRV-2104','INS-1013','Derek','Osborne','IN-CDL-45120091','IN','A','1983-03-08','2020-06-20',13,4,'2026-05-01','Active',false,false,false,1,3,69.7),
('DRV-2105','INS-1013','Nia','Coleman','KY-CDL-22120092','KY','A','1988-11-30','2022-01-10',9,1,'2026-05-01','Active',false,false,false,0,1,86.9),
('DRV-2106','INS-1013','Patrick','Mensah','MI-CDL-11120093','MI','A','1977-07-15','2019-09-01',18,0,'2026-05-01','Active',false,false,true,0,0,91.3),
('DRV-2107','INS-1013','Vince','Alvarado','IN-CDL-45120094','IN','A','1993-02-22','2023-04-15',5,2,'2026-05-01','Active',false,false,false,1,2,74.5),
('DRV-2110','INS-1014','Wayne','Tucker','TN-CDL-88011201','TN','A','1976-08-14','2016-09-01',21,0,'2026-04-01','Active',false,false,false,0,0,94.0),
('DRV-2111','INS-1014','Carla','Simmons','TN-CDL-88011202','TN','A','1984-03-22','2018-05-15',13,1,'2026-04-01','Active',false,false,false,0,1,89.3),
('DRV-2112','INS-1014','Roy','Benton','GA-CDL-66011203','GA','A','1972-11-05','2014-02-10',24,0,'2026-04-01','Active',false,true,false,0,0,95.8),
('DRV-2113','INS-1014','Denise','Fowler','TN-CDL-88011204','TN','A','1990-07-18','2021-08-01',8,2,'2026-04-01','Active',false,false,false,1,2,81.5),
('DRV-2114','INS-1014','Marvin','Ellison','AL-CDL-77011205','AL','A','1981-01-30','2019-06-20',12,3,'2026-04-01','Active',false,false,false,1,3,76.2)""")
print("  drivers: 42")

# COMMAND ----------

# MAGIC %md ## Vehicles (13)

# COMMAND ----------

# DBTITLE 1,Cell 12
spark.sql(f"""INSERT INTO {C}.{S}.vehicles VALUES ('VEH-3001','INS-1001','ACI-AL-25-732053','1XKYDP9X5RJ456789',2023,'Kenworth','T680','Sleeper Tractor',80000,165000.00,'Regional','IL','62704',true,true,'2026-04-15','Pass',115000),
('VEH-3002','INS-1001','ACI-AL-25-732053','3AKJHHDR4NSAB1234',2022,'Freightliner','Cascadia','Sleeper Tractor',80000,148000.00,'Regional','IL','62704',true,true,'2026-04-15','Pass',120000),
('VEH-3003','INS-1001','ACI-AL-25-732053','1XPBDP9X8MD567890',2024,'Peterbilt','579','Day Cab',80000,172000.00,'Intermediate','MO','63101',true,true,'2026-04-15','Pass',95000),
('VEH-3004','INS-1001','ACI-AL-25-732053','5PVNJ8JT2H4S12345',2021,'Volvo','VNL 860','Sleeper Tractor',80000,135000.00,'Regional','IN','46201',true,true,'2026-03-20','Pass',130000),
('VEH-3010','INS-1002','ACI-AL-25-845210','1XKYD49X9PJ789012',2020,'Kenworth','T680','Sleeper Tractor',80000,118000.00,'Long Haul','CA','92335',true,true,'2025-11-10','Pass',145000),
('VEH-3011','INS-1002','ACI-AL-25-845210','3AKJGLDR7LSCD5678',2019,'Freightliner','Cascadia','Sleeper Tractor',80000,95000.00,'Long Haul','CA','92335',false,true,'2025-11-10','Conditional',152000),
('VEH-3012','INS-1002','ACI-AL-25-845210','4V4NC9EH5EN345678',2018,'Volvo','VNR 300','Reefer',54000,82000.00,'Long Haul','AZ','85001',false,true,'2025-09-22','Conditional',138000),
('VEH-3020','INS-1003','ACI-AL-25-690117','1XPYD49X2RJ901234',2024,'Peterbilt','567','Day Cab',80000,185000.00,'Regional','TX','77001',true,true,'2026-05-01','Pass',85000),
('VEH-3021','INS-1003','ACI-AL-25-690117','1XKAD49X6SJ012345',2023,'Kenworth','T880','Day Cab',80000,195000.00,'Regional','TX','77001',true,true,'2026-05-01','Pass',78000),
('VEH-3030','INS-1005','ACI-AL-25-553872','3HSDJAPR8CN567890',2017,'International','LT','Day Cab',73000,62000.00,'Local','TX','75201',false,true,'2025-08-12','Conditional',68000),
('VEH-3031','INS-1005','ACI-AL-25-553872','1HTSDAAN4JH678901',2016,'International','ProStar','Straight Truck',54000,45000.00,'Local','TX','75201',false,true,'2025-08-12','Fail',72000),
('VEH-3040','INS-1006','ACI-AL-25-618934','1XKYDP9X7TJ234567',2024,'Kenworth','T680','Sleeper Tractor',80000,178000.00,'Regional','CO','80201',true,true,'2026-06-01','Pass',105000),
('VEH-3041','INS-1006','ACI-AL-25-618934','3AKJHHDR2RSBC8901',2023,'Freightliner','Cascadia','Sleeper Tractor',80000,158000.00,'Regional','WY','82001',true,true,'2026-06-01','Pass',112000)""")
print("  vehicles: 13")

# COMMAND ----------

# MAGIC %md ## Claims (13)

# COMMAND ----------

# DBTITLE 1,Cell 14
spark.sql(f"""INSERT INTO {C}.{S}.claims VALUES ('CLM-25-2614672','ACI-AL-25-732053','INS-1001','2025-08-12','2025-08-12','Open','Bodily Injury','Rear-end collision at intersection. Third-party soft tissue injury.',80.00,'Jennifer Adams','Mike Patterson',false,'None',45000.00,12000.00,33000.00,3200.00,0.00,false,false,false,NULL),
('CLM-25-2614890','ACI-PD-25-732054','INS-1001','2025-10-03','2025-10-04','Closed','Physical Damage','Tire blowout on I-55; guardrail contact. Vehicle damage only.',100.00,NULL,'Lisa Chang',false,'None',28500.00,28500.00,0.00,1500.00,0.00,false,false,false,'2025-12-15'),
('CLM-24-2389453','ACI-AL-24-732050','INS-1001','2024-11-20','2024-11-21','Closed','Property Damage','Side-swipe in loading dock. Minor third-party vehicle damage.',60.00,'Bob Construction LLC','Mike Patterson',false,'None',8200.00,8200.00,0.00,800.00,3280.00,false,false,false,'2025-02-10'),
('CLM-25-3891045','ACI-AL-25-845210','INS-1002','2025-05-18','2025-05-19','Open','Bodily Injury','Multi-vehicle highway accident on I-10 near Phoenix. Two claimants with moderate injuries. Litigation anticipated.',45.00,'Marcus Rivera','Senior Adjuster Tom Bradley',true,'Suit Filed',385000.00,125000.00,260000.00,45000.00,0.00,false,true,false,NULL),
('CLM-25-3891200','ACI-AL-25-845210','INS-1002','2025-09-22','2025-09-24','Open','Combined','Jackknife on mountain grade. Reefer cargo spoilage plus third-party vehicle damage.',100.00,'Valley Fresh Produce Inc','Tom Bradley',false,'Pre-Suit',142000.00,68000.00,74000.00,12000.00,0.00,false,false,false,NULL),
('CLM-24-3456789','ACI-AL-24-845207','INS-1002','2024-12-05','2024-12-06','Closed','Cargo','Temperature control failure. Full reefer load spoiled. Shipper claim.',100.00,'FreshCo Distribution','Lisa Chang',false,'Settled',89000.00,89000.00,0.00,5500.00,0.00,false,false,false,'2025-04-30'),
('CLM-25-1098234','ACI-AL-25-553872','INS-1005','2025-06-14','2025-06-16','Open','Bodily Injury','Intersection collision. Third party claiming neck/back injury. Late report.',70.00,'Angela Torres','Mike Patterson',true,'Suit Filed',175000.00,35000.00,140000.00,22000.00,0.00,true,false,false,NULL),
('CLM-25-1098567','ACI-AL-25-553872','INS-1005','2025-07-30','2025-08-02','Open','Property Damage','Backing accident at construction site. Damaged equipment.',100.00,'Texas Concrete Supply','Lisa Chang',false,'None',52000.00,32000.00,20000.00,2800.00,0.00,false,false,false,NULL),
('CLM-25-1098891','ACI-AL-25-553872','INS-1005','2025-11-08','2025-11-12','Open','Bodily Injury','Run-off-road incident. Driver fatigue suspected. Pedestrian struck.',90.00,'Robert Nguyen','Senior Adjuster Tom Bradley',true,'Pre-Suit',650000.00,50000.00,600000.00,35000.00,0.00,true,true,true,NULL),
('CLM-25-4521890','ACI-AL-25-778321','INS-1007','2025-04-02','2025-04-03','Open','Bodily Injury','Low-speed rear-end on NJ Turnpike. Claimant alleging disc herniation. Potential nuclear verdict venue.',50.00,'Maria Santangelo','Senior Adjuster Tom Bradley',true,'Suit Filed',420000.00,95000.00,325000.00,58000.00,0.00,false,true,false,NULL),
('CLM-25-4522103','ACI-AL-25-778321','INS-1007','2025-07-19','2025-07-20','Open','Combined','Swoop-and-squat suspected staged collision. Multiple claimants from same vehicle.',25.00,'Multiple (4)','SIU Investigator Olivia Mensah',true,'Pre-Suit',280000.00,0.00,280000.00,18000.00,0.00,true,true,false,NULL),
('CLM-26-5670123','ACI-AL-25-618934','INS-1006','2026-02-14','2026-02-14','Open','Physical Damage','Deer strike on I-25. Bumper and headlight damage only.',0.00,NULL,'Lisa Chang',false,'None',8500.00,0.00,8500.00,500.00,0.00,false,false,false,NULL),
('CLM-23-6789012','ACI-AL-25-690117','INS-1003','2023-03-22','2023-03-22','Closed','Bodily Injury','Tanker rollover on highway. No spill. Third-party vehicle occupant hospitalized with fractures.',75.00,'David Kowalski','Senior Adjuster Tom Bradley',true,'Settled',310000.00,310000.00,0.00,42000.00,0.00,false,true,false,'2024-09-15'),
('CLM-25-7201451','ACI-AL-25-720145','INS-1013','2025-04-12','2025-04-13','Closed','Physical Damage','Low-speed rear-end on I-70; bumper and trailer door damage. Clear liability, insured at fault.',0.00,NULL,'Adjuster Nadia Hassan',false,'None',28000.00,28000.00,0.00,1500.00,0.00,false,false,false,'2025-06-20'),
('CLM-26-7201452','ACI-AL-25-720145','INS-1013','2026-01-30','2026-01-31','Open','Cargo','Load shift damaged palletized goods in transit; salvage of undamaged units pursued.',0.00,NULL,'Cargo Specialist Brett Connolly',false,'None',42000.00,12000.00,30000.00,2500.00,8000.00,false,false,false,NULL),
('CLM-24-5140231','ACI-AL-24-514020','INS-1014','2024-02-10','2024-02-11','Closed','Bodily Injury','Rear-end collision on I-40 in stop-and-go traffic; third-party soft-tissue injury, settled without suit.',70.00,'Gregory Palmer','Adjuster Nadia Hassan',false,'Settled',72000.00,72000.00,0.00,6000.00,0.00,false,false,false,'2024-08-15'),
('CLM-25-5140455','ACI-AL-25-514021','INS-1014','2025-03-18','2025-03-19','Closed','Physical Damage','Weather-related jackknife on I-24 grade; tractor and trailer damage, no third party involved.',100.00,NULL,'Lisa Chang',false,'None',64000.00,64000.00,0.00,3500.00,0.00,false,false,false,'2025-07-01'),
('CLM-25-5140782','ACI-AL-25-514021','INS-1014','2025-11-05','2025-11-07','Open','Bodily Injury','Lane-change sideswipe near Nashville; claimant alleging lumbar injury. Pre-suit demand received.',60.00,'Alicia Mercer','Senior Adjuster Tom Bradley',true,'Pre-Suit',98000.00,40000.00,58000.00,8000.00,0.00,false,false,false,NULL)""")
print("  claims: 18")

# COMMAND ----------

# MAGIC %md ## Submissions (8)

# COMMAND ----------

# DBTITLE 1,Cell 16
spark.sql(f"""INSERT INTO {C}.{S}.submissions VALUES ('SUB-26-11099',NULL,'Rockford Grain Transport LLC','Heartland Specialty Insurance','Tom Berkowitz','2026-06-15','2026-08-01','In Review',28,32,'Regional','Dry Bulk/Grain','1,000,000 CSL',145000.00,NULL,38.20,'David Chen',false,NULL,NULL),
('SUB-26-11102',NULL,'Coastal Petroleum Haulers Inc','Energy Risk Brokers','Rachel Kim','2026-06-20','2026-09-01','Received',15,18,'Intermediate','Petroleum/Chemicals','2,000,000 CSL',280000.00,NULL,25.80,NULL,true,NULL,NULL),
('SUB-26-11087','INS-1014','Dixie Express Lines','Southeast Transport Brokerage','Bill Masters','2026-06-01','2026-08-15','Quoted',52,58,'Long Haul','General Freight','1,000,000 CSL',310000.00,345000.00,52.10,'James Rodriguez',false,NULL,8),
('SUB-26-11078',NULL,'Metro Moving and Storage','Atlantic Specialty Brokers','Linda Garcia','2026-05-20','2026-07-01','Declined',8,10,'Local','Household Goods','1,000,000 CSL',42000.00,NULL,95.30,'Sarah Mitchell',false,'Loss ratio exceeds 90% for 3 consecutive years. Fleet has 2 excluded drivers out of 10 total.',NULL),
('SUB-26-11065','INS-1002','Pacific Coast Carriers Inc','Golden State Insurance Partners','Steve Yamamoto','2026-05-01','2026-07-01','Quoted',42,48,'Long Haul','Refrigerated','1,000,000 CSL',298000.00,325000.00,48.90,'James Rodriguez',true,NULL,12),
('SUB-26-11045',NULL,'Appalachian Coal Transport','Mountain State Risk','Jim Hartley','2026-04-15','2026-06-01','Declined',30,35,'Regional','Coal/Mining','1,000,000 CSL',195000.00,NULL,78.50,'David Chen',true,'CSA Unsafe Driving above 75th percentile. Two DOT OOS inspections in past 6 months. Driver turnover >80%.',NULL),
('SUB-26-11110',NULL,'Precision LTL Carriers','National Fleet Insurance Group','Amy Patel','2026-06-25','2026-09-01','Received',75,82,'Regional','LTL Mixed','1,000,000 CSL',425000.00,NULL,35.40,NULL,false,NULL,NULL),
('SUB-26-10998','INS-1006','Mountain West Freight Systems','Rocky Mountain Risk Partners','Dan Kellogg','2026-03-15','2026-06-15','Bound',65,72,'Regional','General Freight','1,000,000 CSL',345000.00,355000.00,28.70,'David Chen',false,NULL,5),
('SUB-26-12077','INS-1013','Ironhorse Freight Systems LLC','Great Lakes Transport Insurance Brokers','Renata Kowalski','2026-06-25','2026-08-15','In Review',8,8,'Regional','General Freight','1,000,000 CSL',NULL,NULL,66.00,'David Chen',false,NULL,NULL)""")
print("  submissions: 9")

# COMMAND ----------

# MAGIC %md ## Loss Runs (15)

# COMMAND ----------

# DBTITLE 1,Cell 18
spark.sql(f"""INSERT INTO {C}.{S}.loss_runs VALUES ('LR-1001-2325','INS-1001','ACI-AL-23-732047','2023-2024','2024-03-15',4,108200.00,98200.00,10000.00,372000.00,29.10,0,0.05,27050.00),
('LR-1001-2425','INS-1001','ACI-AL-24-732050','2024-2025','2025-03-15',3,142600.00,127800.00,14800.00,398000.00,35.80,0,0.04,47533.33),
('LR-1001-2526','INS-1001','ACI-AL-25-732053','2025-2026','2026-06-15',2,73500.00,40500.00,33000.00,318750.00,23.06,0,0.02,36750.00),
('LR-1002-2324','INS-1002','ACI-AL-24-845207','2023-2024','2024-07-01',2,95000.00,82000.00,13000.00,248000.00,38.30,0,0.05,47500.00),
('LR-1002-2425','INS-1002','ACI-AL-24-845207','2024-2025','2025-07-01',3,134500.00,89000.00,45500.00,275000.00,48.90,0,0.07,44833.33),
('LR-1002-2526','INS-1002','ACI-AL-25-845210','2025-2026','2026-06-15',3,527000.00,193000.00,334000.00,223500.00,235.79,1,0.07,175666.67),
('LR-1003-2324','INS-1003',NULL,'2023-2024','2024-11-20',1,310000.00,310000.00,0.00,480000.00,64.58,1,0.03,310000.00),
('LR-1003-2425','INS-1003','ACI-AL-25-690117','2024-2025','2025-11-20',0,0.00,0.00,0.00,505000.00,0.00,0,0.00,0.00),
('LR-1003-2526','INS-1003','ACI-AL-25-690117','2025-2026','2026-06-15',0,0.00,0.00,0.00,378750.00,0.00,0,0.00,0.00),
('LR-1005-2425','INS-1005','ACI-AL-25-553872','2024-2025','2025-04-01',4,185000.00,145000.00,40000.00,72000.00,256.94,0,0.22,46250.00),
('LR-1005-2526','INS-1005','ACI-AL-25-553872','2025-2026','2026-06-15',3,877000.00,117000.00,760000.00,58500.00,1499.15,2,0.17,292333.33),
('LR-1006-2325','INS-1006','ACI-AL-25-618934','2023-2024','2024-06-15',2,35000.00,35000.00,0.00,310000.00,11.29,0,0.03,17500.00),
('LR-1006-2425','INS-1006','ACI-AL-25-618934','2024-2025','2025-06-15',1,22000.00,22000.00,0.00,330000.00,6.67,0,0.02,22000.00),
('LR-1006-2526','INS-1006','ACI-AL-25-618934','2025-2026','2026-06-15',1,8500.00,0.00,8500.00,258750.00,3.28,0,0.02,8500.00),
('LR-1007-2526','INS-1007','ACI-AL-25-778321','2025-2026','2026-06-15',2,700000.00,95000.00,605000.00,232500.00,301.08,2,0.04,350000.00),
('LR-1013-2324','INS-1013','ACI-AL-23-720140','2023-2024','2024-06-15',2,96000.00,96000.00,0.00,300000.00,32.00,0,0.05,48000.00),
('LR-1013-2425','INS-1013','ACI-AL-24-720142','2024-2025','2025-06-15',4,262000.00,214000.00,48000.00,290000.00,90.34,1,0.09,65500.00),
('LR-1013-2526','INS-1013','ACI-AL-25-720145','2025-2026','2026-06-15',3,205000.00,150000.00,55000.00,300000.00,68.33,0,0.07,68333.33),
('LR-1014-2324','INS-1014','ACI-AL-24-514020','2023-2024','2024-04-01',3,158400.00,158400.00,0.00,330000.00,48.00,0,0.06,52800.00),
('LR-1014-2425','INS-1014','ACI-AL-25-514021','2024-2025','2025-04-01',4,196000.00,168000.00,28000.00,345000.00,56.81,0,0.08,49000.00),
('LR-1014-2526','INS-1014','ACI-AL-25-514021','2025-2026','2026-06-15',3,158000.00,96000.00,62000.00,310000.00,50.97,0,0.06,52666.67)""")
print("  loss_runs: 21")

# COMMAND ----------

# MAGIC %md ## Underwriting Referrals (5)

# COMMAND ----------

# DBTITLE 1,Cell 20
spark.sql(f"""INSERT INTO {C}.{S}.underwriting_referrals VALUES ('REF-26-001','SUB-26-11065',NULL,'INS-1002','2026-05-10','Loss History','VP UW','James Rodriguez','VP Karen Wallace','Approved with Conditions','Rate increase minimum 15%. Add $15K deductible. Require driver DRV-2013 remediation plan within 60 days or exclusion at renewal.','2026-05-14','Three-year trend deteriorating. Large open BI claim CLM-25-3891045 at $385K. Fleet cooperating on safety improvements.'),
('REF-26-002','SUB-26-11102',NULL,'INS-1002','2026-06-22','Risk Appetite','CCO','David Chen',NULL,NULL,NULL,NULL,'HAZMAT fleet, 15 units. Clean history but requires elevated authority per commodity class. Awaiting CCO review.'),
('REF-26-003',NULL,'ACI-AL-25-778321','INS-1007','2026-05-01','CSA Scores','VP UW','Sarah Mitchell','VP Karen Wallace','Declined',NULL,'2026-05-05','Non-renewal recommended. CSA Unsafe Driving 52.1 percentile, Vehicle Maintenance 55.3. Conditional DOT rating. 85% loss ratio current term with two large losses. SIU referral on CLM-25-4522103.'),
('REF-25-015','SUB-26-11045',NULL,'INS-1005','2025-12-10','Loss History','VP UW','David Chen','VP Karen Wallace','Declined',NULL,'2025-12-12','Appalachian Coal: CSA Unsafe Driving above 75th percentile. Two DOT out-of-service inspections in past 6 months. Driver turnover exceeds 80%.'),
('REF-26-004',NULL,'ACI-AL-25-553872','INS-1005','2026-06-01','Loss History','Reserve Committee','James Rodriguez',NULL,NULL,NULL,NULL,'Catastrophic claim CLM-25-1098891 ($650K incurred, fatality). Referring for Reserve Committee review and potential non-renewal. Current-term loss ratio now exceeds 1100%.')""")
print("  underwriting_referrals: 5")

# COMMAND ----------

display(spark.sql(f"""
SELECT 'insureds' AS tbl, COUNT(*) AS n FROM {C}.{S}.insureds
UNION ALL SELECT 'policies', COUNT(*) FROM {C}.{S}.policies
UNION ALL SELECT 'drivers', COUNT(*) FROM {C}.{S}.drivers
UNION ALL SELECT 'vehicles', COUNT(*) FROM {C}.{S}.vehicles
UNION ALL SELECT 'claims', COUNT(*) FROM {C}.{S}.claims
UNION ALL SELECT 'submissions', COUNT(*) FROM {C}.{S}.submissions
UNION ALL SELECT 'loss_runs', COUNT(*) FROM {C}.{S}.loss_runs
UNION ALL SELECT 'underwriting_referrals', COUNT(*) FROM {C}.{S}.underwriting_referrals
ORDER BY tbl
"""))
print("\n✅ Seed data complete")
