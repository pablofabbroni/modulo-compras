import pandas as pd
import io
import re
from datetime import date
import zipfile
import os

def leer_csv_robusto(file_content):
    # Encodings típicos de archivos AFIP/Excel/Windows
    encodings = ["utf-8", "utf-8-sig", "latin-1", "cp1252", "utf-16"]
    # Separadores posibles (AFIP suele venir con ;)
    seps = [None, ";", ",", "\t", "|"]

    last_err = None
    for enc in encodings:
        for sep in seps:
            try:
                # Usamos io.BytesIO para leer el contenido que viene de la web
                df = pd.read_csv(
                    io.BytesIO(file_content),
                    dtype=str,
                    sep=sep,
                    engine="python" if sep is None else "c",
                    encoding=enc
                )
                # print(f"✅ Archivo leído con encoding={enc} | sep={repr(sep)} | columnas={df.shape[1]}")
                return df
            except Exception as e:
                last_err = e
                continue

    raise ValueError(f"No se pudo leer el CSV. Último error: {last_err}")

def preparar_df(df):
    df = df.fillna("")
    n_cols = df.shape[1]
    
    if n_cols == 31:
        tipo = "Comprobantes de importación"
    elif n_cols == 32:
        tipo = "Comprobantes de compras"
    else:
        raise ValueError(f"El archivo tiene {n_cols} columnas. Solo se aceptan 31 o 32.")

    # Columnas que el notebook agrega si no existen
    nuevas_cols = [" CUIT emisor/corredor", "Denominación del emisor/corredor", "IVA comisión"]
    for col in nuevas_cols:
        if col not in df.columns:
            df[col] = ""
            
    return df, tipo

# ---------- Helpers del Notebook ----------

def col_by_letter(letter: str) -> int:
    letter = letter.strip().upper()
    n = 0
    for ch in letter:
        n = n * 26 + (ord(ch) - ord('A') + 1)
    return n - 1

def v(row, letter):
    return row.iloc[col_by_letter(letter)]

def format_fecha_dmy_a_aaaammdd(val):
    s = "" if val is None else str(val).strip()
    if not s:
        return "0" * 8
    m = re.match(r"^(\d{4})-(\d{2})-(\d{2})", s)
    if m:
        y, mm, dd = m.group(1), m.group(2), m.group(3)
        return f"{y}{mm}{dd}"
    if "/" in s:
        parts = s.split("/")
        if len(parts) >= 3:
            try:
                d = int(parts[0])
                mth = int(parts[1])
                y = int(parts[2])
                if mth > 12 and d <= 12:
                    d, mth = mth, d
                return date(y, mth, d).strftime("%Y%m%d")
            except:
                return "0" * 8
    dt = pd.to_datetime(s, dayfirst=True, errors="coerce")
    if pd.isna(dt):
        return "0" * 8
    return dt.strftime("%Y%m%d")

def pad_left_zeros(val, length):
    s = "" if val is None else str(val)
    return s.zfill(length)[:length]

def pad_right_text(val, length):
    s = "" if val is None else str(val)
    s = s[:length]
    return s.ljust(length)

def parse_float(val):
    s = "" if val is None else str(val).strip()
    if s == "":
        return 0.0
    s = s.replace(" ", "")
    if "," in s and "." in s:
        s = s.replace(".", "").replace(",", ".")
    else:
        s = s.replace(",", ".")
    try:
        return float(s)
    except:
        return 0.0

def importe_15(val):
    x = round(parse_float(val), 2)
    return str(int(round(x * 100))).zfill(15)

def tipo_cambio_10(val):
    x = round(parse_float(val), 6)
    return str(int(round(x * 1_000_000))).zfill(10)

def es_distinto_de_cero(val):
    x = parse_float(val)
    return abs(x) > 0.0

# ---------- MODULO COMPRAS ----------

def contar_alicuotas_compras(row):
    grupos = {
        "0%":   ["T"],
        "2.5%": ["U", "V"],
        "5%":   ["W", "X"],
        "10.5%":["Y", "Z"],
        "21%":  ["AA", "AB"],
        "27%":  ["AC", "AD"],
    }
    c = 0
    for cols in grupos.values():
        if any(es_distinto_de_cero(v(row, col)) for col in cols):
            c += 1
    return str(c)

def campo20_importacion(b_val):
    b = str(b_val).strip()
    try:
        b_num = int(b)
    except:
        b_num = None
    return "E" if b_num == 11 else " "

def generar_linea_compras(row):
    campos = []
    campos.append(format_fecha_dmy_a_aaaammdd(v(row, "A")))    
    campos.append(pad_left_zeros(v(row, "B"), 3))              
    campos.append(pad_left_zeros(v(row, "C"), 5))              
    campos.append(pad_left_zeros(v(row, "D"), 20))             
    campos.append("0"*16)                                      
    campos.append(pad_left_zeros(v(row, "E"), 2))              
    campos.append(pad_left_zeros(v(row, "F"), 20))             
    campos.append(pad_right_text(v(row, "G"), 30))             
    campos.append(importe_15(v(row, "H")))                      
    campos.append(importe_15(v(row, "K")))  
    campos.append(importe_15(v(row, "L")))  
    campos.append(importe_15(v(row, "Q")))  
    campos.append(importe_15(v(row, "N")))  
    campos.append(importe_15(v(row, "O")))  
    campos.append(importe_15(v(row, "P")))  
    campos.append(importe_15(v(row, "R")))  
    campos.append("PES")
    campos.append(tipo_cambio_10(1))   
    campos.append(contar_alicuotas_compras(row))                       
    campos.append(campo20_importacion(v(row, "B")))                                         
    campos.append(importe_15(v(row, "M")))                      
    campos.append(importe_15(v(row, "S")))                      
    campos.append(pad_left_zeros(v(row, "AG"), 11))            
    campos.append(pad_right_text(v(row, "AH"), 30))            
    campos.append(importe_15(v(row, "AI")))                    
    linea = "".join(campos)
    return linea

ALICUOTAS_COMPRAS = [
    {"rate": "0",    "neto_col": "T",  "iva_col": None, "codigo": "0003"},
    {"rate": "2.5",  "neto_col": "U",  "iva_col": "V", "codigo": "0009"},
    {"rate": "5",    "neto_col": "W",  "iva_col": "X", "codigo": "0008"},
    {"rate": "10.5", "neto_col": "Y",  "iva_col": "Z", "codigo": "0004"},
    {"rate": "21",   "neto_col": "AA", "iva_col": "AB","codigo": "0005"},
    {"rate": "27",   "neto_col": "AC", "iva_col": "AD","codigo": "0006"},
]

def generar_linea_alicuota_compras(row, spec):
    c1 = pad_left_zeros(v(row, "B"), 3)    
    c2 = pad_left_zeros(v(row, "C"), 5)    
    c3 = pad_left_zeros(v(row, "D"), 20)   
    c4 = pad_left_zeros(v(row, "E"), 2)    
    c5 = pad_left_zeros(v(row, "F"), 20)   
    c6 = importe_15(v(row, spec["neto_col"]))  
    c7 = spec["codigo"]  
    if spec["iva_col"] is None:
        c8 = "0" * 15
    else:
        c8 = importe_15(v(row, spec["iva_col"]))
    return f"{c1}{c2}{c3}{c4}{c5}{c6}{c7}{c8}"

def generar_lineas_alicuotas_compras(row):
    lineas = []
    for spec in ALICUOTAS_COMPRAS:
        neto = v(row, spec["neto_col"])
        iva = "0" if spec["iva_col"] is None else v(row, spec["iva_col"])
        if es_distinto_de_cero(neto) or es_distinto_de_cero(iva):
            lineas.append(generar_linea_alicuota_compras(row, spec))
    return lineas

# ---------- MODULO IMPORTACION ----------

def contar_alicuotas_importacion(row):
    grupos = {
        "0%":   ["S"],
        "2.5%": ["T", "U"],
        "5%":   ["V", "W"],
        "10.5%":["X", "Y"],
        "21%":  ["Z", "AA"],
        "27%":  ["AB", "AC"],
    }
    c = 0
    for cols in grupos.values():
        if any(es_distinto_de_cero(v(row, col)) for col in cols):
            c += 1
    return str(c)

def generar_linea_importacion(row):
    campos = []
    campos.append(format_fecha_dmy_a_aaaammdd(v(row, "A")))   # 1
    campos.append(pad_left_zeros(v(row, "B"), 3))             # 2
    campos.append("00000")                                    # 3
    campos.append("0"*20)                                     # 4
    campos.append(pad_left_zeros(v(row, "C"), 16))            # 5
    campos.append(pad_left_zeros(v(row, "D"), 2))             # 6
    campos.append(pad_left_zeros(v(row, "E"), 20))            # 7
    campos.append(pad_right_text(v(row, "F"), 30))            # 8
    campos.append(importe_15(v(row, "G")))                    # 9
    campos.append(importe_15(v(row, "J")))  
    campos.append(importe_15(v(row, "K")))  
    campos.append(importe_15(v(row, "P")))  
    campos.append(importe_15(v(row, "M")))  
    campos.append(importe_15(v(row, "N")))  
    campos.append(importe_15(v(row, "O")))  
    campos.append(importe_15(v(row, "Q")))  
    campos.append("PES")                   
    campos.append(tipo_cambio_10(1))       
    campos.append(contar_alicuotas_importacion(row))          
    campos.append(campo20_importacion(v(row, "B")))           
    campos.append(importe_15(v(row, "L")))                    
    campos.append(importe_15(v(row, "R")))                    
    campos.append(pad_left_zeros(v(row, "AF"), 11))           
    campos.append(pad_right_text(v(row, "AG"), 30))           
    campos.append(importe_15(v(row, "AH")))                   
    return "".join(campos)

ALICUOTAS_IMPORT = [
    {"neto_col": "S", "iva_col": None, "codigo": "0003"},
    {"neto_col": "T", "iva_col": "U",  "codigo": "0009"},
    {"neto_col": "V", "iva_col": "W",  "codigo": "0008"},
    {"neto_col": "X", "iva_col": "Y",  "codigo": "0004"},
    {"neto_col": "Z", "iva_col": "AA", "codigo": "0005"},
    {"neto_col": "AB", "iva_col": "AC","codigo": "0006"},
]

def generar_linea_alicuota_import(row, spec):
    # La estructura suele ser similar a compras pero validamos columnas si es necesario
    c1 = pad_left_zeros(v(row, "B"), 3)    
    c2 = "00000" # Fijo para impo
    c3 = "0"*20  # Fijo para impo
    c4 = pad_left_zeros(v(row, "D"), 2)    
    c5 = pad_left_zeros(v(row, "E"), 20)   
    c6 = importe_15(v(row, spec["neto_col"]))  
    c7 = spec["codigo"]  
    if spec["iva_col"] is None:
        c8 = "0" * 15
    else:
        c8 = importe_15(v(row, spec["iva_col"]))
    return f"{c1}{c2}{c3}{c4}{c5}{c6}{c7}{c8}"

def generar_lineas_alicuotas_import(row):
    lineas = []
    for spec in ALICUOTAS_IMPORT:
        neto = v(row, spec["neto_col"])
        iva = "0" if spec["iva_col"] is None else v(row, spec["iva_col"])
        if es_distinto_de_cero(neto) or es_distinto_de_cero(iva):
            lineas.append(generar_linea_alicuota_import(row, spec))
    return lineas

# ---------- PROCESAMIENTO GENERAL ----------

def procesar_csv(df, tipo):
    files_to_zip = {}
    
    if tipo == "Comprobantes de compras":
        # CBTE
        lineas_cbte = [generar_linea_compras(df.iloc[idx]) for idx in range(len(df))]
        files_to_zip["LIBRO_IVA_DIGITAL_COMPRAS_CBTE.txt"] = "\n".join(lineas_cbte)
        
        # ALICUOTAS
        lineas_aliq = []
        for idx in range(len(df)):
            lineas_aliq.extend(generar_lineas_alicuotas_compras(df.iloc[idx]))
        files_to_zip["LIBRO_IVA_DIGITAL_COMPRAS_ALICUOTAS.txt"] = "\n".join(lineas_aliq)
        
    elif tipo == "Comprobantes de importación":
        # CBTE
        lineas_cbte = [generar_linea_importacion(df.iloc[idx]) for idx in range(len(df))]
        files_to_zip["LIBRO_IVA_DIGITAL_IMPORTACION_CBTE.txt"] = "\n".join(lineas_cbte)
        
        # ALICUOTAS
        lineas_aliq = []
        for idx in range(len(df)):
            lineas_aliq.extend(generar_lineas_alicuotas_import(df.iloc[idx]))
        files_to_zip["LIBRO_IVA_DIGITAL_IMPORTACION_BIENES_ALICUOTA.txt"] = "\n".join(lineas_aliq)
        
    return files_to_zip

def crear_zip(files_dict):
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as z:
        for filename, content in files_dict.items():
            z.writestr(filename, content)
    zip_buffer.seek(0)
    return zip_buffer
