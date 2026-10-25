USE master;
GO

IF DB_ID('TaskFlowDB') IS NOT NULL
BEGIN
    ALTER DATABASE TaskFlowDB SET SINGLE_USER WITH ROLLBACK IMMEDIATE;
    DROP DATABASE TaskFlowDB;
END;
GO

CREATE DATABASE TaskFlowDB;
GO

USE TaskFlowDB;
GO


CREATE TABLE Empresa (
    id_empresa INT IDENTITY(1,1) PRIMARY KEY,
    nombre_empresa VARCHAR(50) NOT NULL UNIQUE,
    rnc VARCHAR(20) NOT NULL UNIQUE,
    fecha_registro DATE NOT NULL DEFAULT GETDATE()
);
GO

CREATE TABLE Rol (
    id_rol INT IDENTITY(1,1) PRIMARY KEY,
    nombre_rol VARCHAR(30) NOT NULL UNIQUE
);
GO


CREATE TABLE Departamento (
    id_departamento INT IDENTITY(1,1) PRIMARY KEY,
    nombre_depto VARCHAR(30) NOT NULL,
    id_empresa INT NOT NULL,
    CONSTRAINT FK_Departamento_Empresa FOREIGN KEY (id_empresa)
        REFERENCES Empresa(id_empresa)
);
GO


CREATE TABLE Puesto (
    id_puesto INT IDENTITY(1,1) PRIMARY KEY,
    nombre_puesto VARCHAR(30) NOT NULL,
    id_departamento INT NOT NULL,
    CONSTRAINT FK_Puesto_Departamento FOREIGN KEY (id_departamento)
        REFERENCES Departamento(id_departamento)
);
GO


CREATE TABLE Usuario (
    id_usuario INT IDENTITY(1,1) PRIMARY KEY,
    codigo_usuario VARCHAR(10) NOT NULL UNIQUE,
    nombres VARCHAR(30) NOT NULL,
    apellidos VARCHAR(30) NOT NULL,
    correo VARCHAR(50) NOT NULL UNIQUE,
    contrasena VARCHAR(64) NOT NULL, 
    id_rol INT NOT NULL,
    id_empresa INT NULL,        
    id_departamento INT NULL,
    id_puesto INT NULL,
    id_jefe INT NULL,
    fecha_ingreso DATE NOT NULL DEFAULT GETDATE(),
    estado VARCHAR(15) DEFAULT 'Activo' NOT NULL,
    CONSTRAINT FK_Usuario_Rol FOREIGN KEY (id_rol) REFERENCES Rol(id_rol),
    CONSTRAINT FK_Usuario_Empresa FOREIGN KEY (id_empresa) REFERENCES Empresa(id_empresa),
    CONSTRAINT FK_Usuario_Departamento FOREIGN KEY (id_departamento) REFERENCES Departamento(id_departamento),
    CONSTRAINT FK_Usuario_Puesto FOREIGN KEY (id_puesto) REFERENCES Puesto(id_puesto),
    CONSTRAINT FK_Usuario_Jefe FOREIGN KEY (id_jefe) REFERENCES Usuario(id_usuario)
);
GO


CREATE TABLE Prioridad (
    id_prioridad INT IDENTITY(1,1) PRIMARY KEY,
    nivel_prioridad VARCHAR(15) NOT NULL UNIQUE
);
GO

CREATE TABLE EstadoTarea (
    id_estado_tarea INT IDENTITY(1,1) PRIMARY KEY,
    nombre_estado VARCHAR(20) NOT NULL UNIQUE
);
GO


CREATE TABLE Tarea (
    id_tarea INT IDENTITY(1,1) PRIMARY KEY,
    codigo_tarea VARCHAR(10) NOT NULL UNIQUE,
    titulo VARCHAR(30) NOT NULL,
    descripcion VARCHAR(255) NULL,
    id_empresa INT NOT NULL,
    id_departamento INT NOT NULL,
    id_usuario_asignado INT NOT NULL,
    id_usuario_creador INT NOT NULL,
    id_prioridad INT NOT NULL,
    id_estado_tarea INT NOT NULL,
    fecha_creacion DATE NOT NULL DEFAULT GETDATE(),
    fecha_vencimiento DATE NOT NULL,
    CONSTRAINT FK_Tarea_Empresa FOREIGN KEY (id_empresa) REFERENCES Empresa(id_empresa),
    CONSTRAINT FK_Tarea_Departamento FOREIGN KEY (id_departamento) REFERENCES Departamento(id_departamento),
    CONSTRAINT FK_Tarea_Asignado FOREIGN KEY (id_usuario_asignado) REFERENCES Usuario(id_usuario),
    CONSTRAINT FK_Tarea_Creador FOREIGN KEY (id_usuario_creador) REFERENCES Usuario(id_usuario),
    CONSTRAINT FK_Tarea_Prioridad FOREIGN KEY (id_prioridad) REFERENCES Prioridad(id_prioridad),
    CONSTRAINT FK_Tarea_Estado FOREIGN KEY (id_estado_tarea) REFERENCES EstadoTarea(id_estado_tarea)
);
GO


CREATE TABLE Mensaje (
    id_mensaje INT IDENTITY(1,1) PRIMARY KEY,
    id_emisor INT NOT NULL,
    id_receptor INT NOT NULL,
    contenido VARCHAR(255) NOT NULL,
    fecha_envio DATETIME NOT NULL DEFAULT GETDATE(),
    leido BIT DEFAULT 0 NOT NULL,
    CONSTRAINT FK_Mensaje_Emisor FOREIGN KEY (id_emisor) REFERENCES Usuario(id_usuario),
    CONSTRAINT FK_Mensaje_Receptor FOREIGN KEY (id_receptor) REFERENCES Usuario(id_usuario)
);
GO

-- Inserción de Roles (ID 1 al 5)
INSERT INTO Rol (nombre_rol) VALUES 
('SuperAdmin'),        -- ID: 1
('Admin de Empresa'), -- ID: 2 (Nuevo: Acceso total a nivel de empresa, puesto solo por SuperAdmin)
('Dueño'),             -- ID: 3
('Jefe Departamento'), -- ID: 4
('Empleado');          -- ID: 5
GO

INSERT INTO Prioridad (nivel_prioridad) VALUES 
('Vital'), ('Alta'), ('Baja'), ('Muy Baja');
GO

INSERT INTO EstadoTarea (nombre_estado) VALUES 
('Sin Iniciar'), ('En Proceso'), ('Completada'), ('No Realizada');
GO

-- SuperAdmin inicial (Clave: superadmin123)
INSERT INTO Usuario (codigo_usuario, nombres, apellidos, correo, contrasena, id_rol, id_empresa, id_departamento, id_puesto, id_jefe, fecha_ingreso, estado)
VALUES (
    'ROOT-01', 'Administrador', 'Global', 'admin@taskflow.com',
    CONVERT(VARCHAR(64), HASHBYTES('SHA2_256', 'superadmin123'), 2),
    1, NULL, NULL, NULL, NULL, GETDATE(), 'Activo'
);
GO