import os
import pandas as pd
import streamlit as st

# Configuración de la página
st.set_page_config(
    page_title="Gestión de Inventarios", page_icon="📦", layout="wide"
)

# Archivo local para persistencia de datos
EXCEL_FILE = "inventario_data.xlsx"


@st.cache_data
def cargar_datos():
  if os.path.exists(EXCEL_FILE):
    return pd.read_excel(EXCEL_FILE)
  else:
    # DataFrame inicial por defecto si no existe el archivo
    df_default = pd.DataFrame(
        columns=[
            "ID",
            "Producto",
            "Categoría",
            "Cantidad",
            "Precio Unitario ($)",
            "Ubicación",
        ]
    )
    df_default.to_excel(EXCEL_FILE, index=False)
    return df_default


def guardar_datos(df):
  df.to_excel(EXCEL_FILE, index=False)


# Cargar datos actuales
df_inventario = cargar_datos()

# Título principal
st.title("📦 Sistema de Gestión de Inventarios")
st.markdown("Administra tus productos, controla el stock y exporta tus datos.")

# Sidebar para navegación
menu = st.sidebar.selectbox(
    "Menú de Navegación",
    [
        "Ver Inventario",
        "Agregar Producto",
        "Actualizar Stock",
        "Eliminar Producto",
    ],
)

# 1. VER INVENTARIO
if menu == "Ver Inventario":
  st.subheader("📋 Inventario Actual")

  if df_inventario.empty:
    st.info("No hay productos registrados en el inventario.")
  else:
    # Filtros de búsqueda
    busqueda = st.text_input("🔍 Buscar producto por nombre o categoría:")
    if busqueda:
      df_filtrado = df_inventario[
          df_inventario["Producto"]
          .str.contains(busqueda, case=False, na=False)
          | df_inventario["Categoría"]
          .str.contains(busqueda, case=False, na=False)
      ]
    else:
      df_filtrado = df_inventario

    # Mostrar métricas rápidas
    col1, col2, col3 = st.columns(3)
    col1.metric("Total de Productos Únicos", len(df_inventario))
    col2.metric("Unidades Totales en Stock", int(df_inventario["Cantidad"].sum()))
    valor_total = (
        df_inventario["Cantidad"] * df_inventario["Precio Unitario ($)"]
    ).sum()
    col3.metric("Valor Total del Inventario", f"${valor_total:,.2f}")

    # Tabla interactiva
    st.dataframe(df_filtrado, use_container_width=True)

    # Botón de descarga Excel
    with open(EXCEL_FILE, "rb") as f:
      st.download_button(
          label="📥 Descargar Inventario en Excel",
          data=f,
          file_name="inventario.xlsx",
          mime=(
              "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
          ),
      )

# 2. AGREGAR PRODUCTO
elif menu == "Agregar Producto":
  st.subheader("➕ Registrar Nuevo Producto")

  with st.form("form_agregar"):
    col1, col2 = st.columns(2)
    with col1:
      prod_id = st.text_input("ID / Código de Barras")
      nombre = st.text_input("Nombre del Producto")
      categoria = st.text_input("Categoría")
    with col2:
      cantidad = st.number_input("Cantidad Inicial", min_value=0, step=1)
      precio = st.number_input(
          "Precio Unitario ($)", min_value=0.0, format="%.2f"
      )
      ubicacion = st.text_input("Ubicación en Almacén")

    submitted = st.form_submit_button("Guardar Producto")

    if submitted:
      if not prod_id or not nombre:
        st.warning(
            "Por favor, completa al menos el ID y el Nombre del producto."
        )
      elif prod_id in df_inventario["ID"].astype(str).values:
        st.error(f"El ID '{prod_id}' ya existe en el inventario.")
      else:
        nuevo_registro = pd.DataFrame({
            "ID": [prod_id],
            "Producto": [nombre],
            "Categoría": [categoria],
            "Cantidad": [int(cantidad)],
            "Precio Unitario ($)": [float(precio)],
            "Ubicación": [ubicacion],
        })
        df_inventario = pd.concat(
            [df_inventario, nuevo_registro], ignore_index=True
        )
        guardar_datos(df_inventario)
        st.success(f"¡Producto '{nombre}' agregado exitosamente!")

# 3. ACTUALIZAR STOCK
elif menu == "Actualizar Stock":
  st.subheader("🔄 Actualizar Cantidad de Stock")

  if df_inventario.empty:
    st.info("No hay productos disponibles para actualizar.")
  else:
    producto_seleccionado = st.selectbox(
        "Seleccione el Producto", df_inventario["Producto"].values
    )

    # Obtener datos actuales del producto
    idx = df_inventario[
        df_inventario["Producto"] == producto_seleccionado
    ].index[0]
    stock_actual = int(df_inventario.loc[idx, "Cantidad"])

    st.write(f"Stock actual disponible: **{stock_actual} unidades**")

    tipo_movimiento = st.radio(
        "Tipo de Operación",
        ["Entrada (Sumar)", "Salida (Restar)", "Definir Stock Fijo"],
    )
    cantidad_cambio = st.number_input("Cantidad", min_value=1, step=1)

    if st.button("Aplicar Cambios"):
      if tipo_movimiento == "Entrada (Sumar)":
        nuevo_stock = stock_actual + cantidad_cambio
      elif tipo_movimiento == "Salida (Restar)":
        nuevo_stock = max(0, stock_actual - cantidad_cambio)
      else:
        nuevo_stock = cantidad_cambio

      df_inventario.loc[idx, "Cantidad"] = nuevo_stock
      guardar_datos(df_inventario)
      st.success(
          f"¡Stock actualizado! El nuevo inventario de '{producto_seleccionado}'"
          f" es {nuevo_stock} unidades."
      )
      st.rerun()

# 4. ELIMINAR PRODUCTO
elif menu == "Eliminar Producto":
  st.subheader("🗑️ Eliminar Producto del Inventario")

  if df_inventario.empty:
    st.info("No hay productos para eliminar.")
  else:
    producto_a_eliminar = st.selectbox(
        "Seleccione el producto a eliminar", df_inventario["Producto"].values
    )

    if st.button("Eliminar Permanentemente", type="primary"):
      df_inventario = df_inventario[
          df_inventario["Producto"] != producto_a_eliminar
      ]
      guardar_datos(df_inventario)
      st.success(
          f"El producto '{producto_a_eliminar}' ha sido eliminado del"
          " inventario."
      )
      st.rerun()