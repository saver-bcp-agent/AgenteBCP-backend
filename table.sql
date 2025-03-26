DROP TABLE IF EXISTS ahorros;

CREATE TABLE ahorros (
    id SERIAL PRIMARY KEY,
    usuario_id TEXT NOT NULL, 
    meta TEXT NOT NULL, 
    ingreso_mensual DECIMAL(10,2) NOT NULL,
    ahorro_sugerido DECIMAL(10,2), 
    ahorro_confirmado DECIMAL(10,2),
    fecha TIMESTAMP DEFAULT NOW() 
);

INSERT INTO ahorros (usuario_id, meta, ingreso_mensual, ahorro_sugerido, ahorro_confirmado)
VALUES ('1', 'Viaje a Cusco', 2000.00, 100.00, 100.00);
