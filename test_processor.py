import pandas as pd
from app.processor import preparar_df, generar_linea_compras, generar_lineas_alicuotas_compras

# Mock data for Compras (32 columns)
columns = [chr(65+i) for i in range(26)] + ["AA", "AB", "AC", "AD", "AE", "AF"]
data = [["" for _ in range(32)]]
data[0][0] = "01/02/2026"  # A: Fecha
data[0][1] = "11"          # B: Tipo
data[0][2] = "3"           # C: Punto Venta
data[0][3] = "6564"        # D: Numero
data[0][4] = "80"          # E: Tipo Doc
data[0][5] = "20344538485" # F: Nro Doc
data[0][6] = "KEINER"      # G: Denominacion
data[0][7] = "9398"        # H: Importe Total
data[0][10] = "0"          # K: Neto
data[0][11] = "0"          # L: Neto
data[0][16] = "0"          # Q: Neto
data[0][13] = "0"          # N: Neto
data[0][14] = "0"          # O: Neto
data[0][15] = "0"          # P: Neto
data[0][17] = "0"          # R: Neto

# Alicuota 21%
data[0][26] = "100"        # AA: Neto 21%
data[0][27] = "21"         # AB: IVA 21%

df = pd.DataFrame(data, columns=columns)
print(f"Mock DF shape: {df.shape}")

df_prepared, tipo = preparar_df(df)
print(f"Tipo detectado: {tipo}")

linea_cbte = generar_linea_compras(df_prepared.iloc[0])
print(f"Línea CBTE (325 chars?): {len(linea_cbte)}")

lineas_aliq = generar_lineas_alicuotas_compras(df_prepared.iloc[0])
print(f"Líneas Alicuotas: {len(lineas_aliq)}")
if len(lineas_aliq) > 0:
    print(f"Línea Aliq (84 chars?): {len(lineas_aliq[0])}")

print("Verificación Básica Exitosa!")
