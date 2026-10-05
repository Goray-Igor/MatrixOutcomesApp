USE MatrixOutcomesDB;
GO

-- 1. Видаляємо існуючі зв'язки та таблиці
DECLARE @sql NVARCHAR(MAX) = N'';
SELECT @sql += N'ALTER TABLE ' + QUOTENAME(OBJECT_SCHEMA_NAME(parent_object_id)) 
    + '.' + QUOTENAME(OBJECT_NAME(parent_object_id)) 
    + ' DROP CONSTRAINT ' + QUOTENAME(name) + ';' + CHAR(13)
FROM sys.foreign_keys
WHERE referenced_object_id IN (
    OBJECT_ID('tbl_MainRegistry'), OBJECT_ID('tbl_Manager_Results'), OBJECT_ID('tbl_LandOfficer_Decisions')
);
EXEC sp_executesql @sql;
GO

DROP TABLE IF EXISTS tbl_LandOfficer_Decisions;
DROP TABLE IF EXISTS tbl_Manager_Results;
DROP TABLE IF EXISTS tbl_MainRegistry;
GO

-- 2. Створюємо оновлену таблицю
CREATE TABLE tbl_MainRegistry (
    RecordUID NVARCHAR(255) PRIMARY KEY, -- Унікальний ключ: Договір + Кадастр (або індекс)
    CadastralNumber NVARCHAR(100) NULL,  -- ТЕПЕР МОЖЕ БУТИ NULL
    AgreementUID NVARCHAR(100),
    ContractNumber NVARCHAR(100),
    
    Village NVARCHAR(255),
    Cluster NVARCHAR(255),
    MainOrg NVARCHAR(255),
    FieldNumber NVARCHAR(100),
    CurrentCrop NVARCHAR(100),
    
    CounterpartyName NVARCHAR(255),
    INN NVARCHAR(20),
    
    ContractDate DATE,
    ExpiryDate DATE,
    TermYears INT,
    ContractType NVARCHAR(255),
    LessorType NVARCHAR(100),
    
    Area DECIMAL(18, 4),
    PlotType NVARCHAR(100),
    ShareCount DECIMAL(18, 4),
    ShareNumber NVARCHAR(50),
    RegStatus NVARCHAR(100),
    PlotStatus NVARCHAR(100),
    
    CropProject NVARCHAR(100) DEFAULT '-',
    
    -- НОВІ АТРИБУТИ
    LessorIntent NVARCHAR(255) NULL,     -- Намір орендодавця
    IntentLetterDate DATE NULL           -- Дата листа наміру
);
GO

-- 3. Відновлюємо таблиці результатів (без змін у структурі)
CREATE TABLE tbl_Manager_Results (
    ResultID INT IDENTITY(1,1) PRIMARY KEY,
    RecordUID NVARCHAR(255) FOREIGN KEY REFERENCES tbl_MainRegistry(RecordUID),
    ManagerID INT FOREIGN KEY REFERENCES tbl_Users(UserID),
    Outcome NVARCHAR(50),
    ProcessingStatus NVARCHAR(50),
    ExitOrder NVARCHAR(100),
    CompetitorName NVARCHAR(255),
    ContactType NVARCHAR(50),
    ContactInfo NVARCHAR(255),
    Comment NVARCHAR(MAX),
    IsConflict BIT DEFAULT 0,
    UpdatedAt DATETIME DEFAULT GETDATE()
);

CREATE TABLE tbl_LandOfficer_Decisions (
    DecisionID INT IDENTITY(1,1) PRIMARY KEY,
    RecordUID NVARCHAR(255) FOREIGN KEY REFERENCES tbl_MainRegistry(RecordUID),
    OfficerID INT FOREIGN KEY REFERENCES tbl_Users(UserID),
    RemovedCadastralNumbers NVARCHAR(MAX),
    RemovedVillage NVARCHAR(255),
    RemovedField NVARCHAR(100),
    RemovedShareNumber NVARCHAR(50),
    RemovedArea DECIMAL(18, 4),
    Counterparty NVARCHAR(255),
    Comment NVARCHAR(MAX),
    BoundarySettingDate DATE NULL,
    TerminationDate1C DATE NULL,
    DecisionDate DATETIME DEFAULT GETDATE()
);
GO