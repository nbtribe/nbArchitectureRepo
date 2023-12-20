

--This will create your demo table
CREATE TABLE personal_health_identifiable_information (
    mpi char (10),
    firstName VARCHAR (30),
    lastName VARCHAR (30),
    email VARCHAR (75),
    gender CHAR (10),
    mobileNumber VARCHAR(20),
    clinicId VARCHAR(10),
    creditCardNumber VARCHAR(50),
    driverLicenseNumber VARCHAR(40),
    patientJobTitle VARCHAR(100),
    ssn VARCHAR(15),
    geo VARCHAR(250),
    mbi VARCHAR(50)    
);



--this will load your demo table
COPY personal_health_identifiable_information
FROM 's3://<S3BucketName>/personal_health_identifiable_information.csv'
IAM_ROLE '<RedshiftRoleArn>'
CSV
delimiter ','
region '<aws region>'
IGNOREHEADER 1;