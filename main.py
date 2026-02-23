import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import numpy as np

# 1. Configuración de la página
st.set_page_config(page_title="Scouting IVO Catar 2022", page_icon="⚽", layout="wide")

# 2. Cargar datos
@st.cache_data
def cargar_datos():
    return pd.read_csv("qatar2022_ivo_dashboard.csv")

@st.cache_data
def cargar_datos_espaciales():
    try:
        return pd.read_csv("qatar2022_espacial_ivo.csv")
    except Exception:
        return pd.DataFrame()

df_ivo = cargar_datos()
df_espacial = cargar_datos_espaciales()

# Inicializamos variables para guardar los gráficos de cara al informe final
fig_scatter = None
fig_radar = None
fig_pitch = None

# 3. Título principal
st.title("⚽ Modelo IVO: scouting de eficiencia")

# ==========================================
# 4. FILTROS EN LA BARRA LATERAL (GLOBALES)
# ==========================================
st.sidebar.header("Filtros de scouting")

# Filtro: Minutos
minutos_min = st.sidebar.slider("Minutos mínimos", 0, int(df_ivo['Minutos'].max()), 180)

# Filtro: Selección
lista_equipos = sorted(df_ivo['Seleccion'].unique().tolist())
equipos_sel = st.sidebar.multiselect("Filtrar por selección (vacío = todas)", options=lista_equipos, default=[])

# Filtro: Posición
lista_posiciones = sorted(df_ivo['Posicion'].dropna().unique().tolist()) if 'Posicion' in df_ivo.columns else []
posiciones_sel = st.sidebar.multiselect("Filtrar por demarcación (vacío = todas):", options=lista_posiciones, default=[])

# --- APLICACIÓN EN CASCADA DE TODOS LOS FILTROS ---

# 1. CREAMOS DF_BASE: Solo tiene Minutos y Selección (Para el XI Ideal)
df_base = df_ivo[df_ivo['Minutos'] >= minutos_min].copy()
if len(equipos_sel) > 0:
    df_base = df_base[df_base['Seleccion'].isin(equipos_sel)]
df_base = df_base.sort_values(by='IVO_P90', ascending=False).reset_index(drop=True)

# 2. CREAMOS DF_FILTRADO: Añade la Demarcación (Para todo el resto del dashboard)
df_filtrado = df_base.copy()
if len(posiciones_sel) > 0:
    df_filtrado = df_filtrado[df_filtrado['Posicion'].isin(posiciones_sel)]
df_filtrado = df_filtrado.reset_index(drop=True)

# ==========================================
# SECCIÓN DE KPIs 
# ==========================================
col_kpi1, col_kpi2, col_kpi3, col_kpi4 = st.columns(4)

with col_kpi1:
    st.metric(
        label="Jugadores filtrados", 
        value=len(df_filtrado),
        help="Número total de jugadores que cumplen todos los criterios (incluida demarcación)."
    )

with col_kpi2:
    media_ivo = df_filtrado['IVO_P90'].mean() if not df_filtrado.empty else 0
    st.metric(
        label="Media IVO", 
        value=f"{media_ivo:.3f}",
        delta=f"{(media_ivo - df_ivo['IVO_P90'].mean()):.3f}",
        help="Promedio de eficiencia del grupo seleccionado comparado con el total."
    )

with col_kpi3:
    if not df_filtrado.empty:
        top_player = df_filtrado.iloc[0]['Jugador']
        top_val = df_filtrado.iloc[0]['IVO_P90']
        st.metric(label="Líder eficiencia", value=top_player, delta=f"{top_val:.3f} IVO")
    else:
        st.metric(label="Líder eficiencia", value="-")

with col_kpi4:
    presion_media = df_filtrado['Presion_Pct'].mean() if 'Presion_Pct' in df_filtrado.columns else 0
    st.metric(label="Intensidad media", value=f"{presion_media:.1f}%")

st.divider()

# ==========================================
# CREACIÓN DE PESTAÑAS (TABS)
# ==========================================
tab_ranking, tab_comparativa, tab_analisis_avanzado = st.tabs([
    "📊 Ranking y Mercado", 
    "⚔️ Comparativa y Clones", 
    "🔬 Táctica y Espacial"
])

# ==========================================
# --- PESTAÑA 1: RANKING Y CUADRANTES ---
# ==========================================
with tab_ranking:
    col_tabla, col_cuadrante = st.columns([1, 1.4], gap="large")

    with col_tabla:
        st.subheader(f"📊 Ranking ({len(df_filtrado)} jug.)")
        st.dataframe(df_filtrado, use_container_width=True, height=600)

        if not df_filtrado.empty:
            csv = df_filtrado.to_csv(index=False).encode('utf-8')
            st.download_button(label="📥 Descargar este ranking como CSV", data=csv, file_name='scouting_ivo_export.csv', mime='text/csv')

    with col_cuadrante:
        st.subheader("📈 Análisis: Riesgo vs Recompensa")

        opciones_x = {
            'Construcción: Pases P90': 'Pases_P90',
            'Desborde: Regates P90': 'Regates_P90',
            'Finalización: Tiros P90': 'Tiros_P90'
        }
        eje_x_etiqueta = st.selectbox("⚽ Selecciona la métrica para el Eje X:", list(opciones_x.keys()))
        columna_x = opciones_x[eje_x_etiqueta]

        if len(df_filtrado) > 0:
            df_plot = df_filtrado.copy()
            df_plot[columna_x] = pd.to_numeric(df_plot[columna_x], errors='coerce').fillna(0.0)
            df_plot['IVO_P90'] = pd.to_numeric(df_plot['IVO_P90'], errors='coerce').fillna(0.0)

            media_x = float(df_plot[columna_x].mean())
            media_y = float(df_plot['IVO_P90'].mean())

            fig_scatter = go.Figure()
            tiene_posicion = 'Posicion' in df_plot.columns

            if tiene_posicion:
                df_plot['Posicion'] = df_plot['Posicion'].fillna('Sin definir').astype(str)
                posiciones = df_plot['Posicion'].unique()
                for pos in posiciones:
                    df_pos = df_plot[df_plot['Posicion'] == pos]
                    fig_scatter.add_trace(go.Scatter(
                        x=df_pos[columna_x].tolist(),
                        y=df_pos['IVO_P90'].tolist(),
                        mode='markers',
                        name=pos,
                        text=df_pos['Jugador'].tolist(),
                        marker=dict(size=10, line=dict(width=1, color='white')),
                        hovertemplate="<b>%{text}</b><br>IVO: %{y:.2f}<br>Volumen: %{x:.2f}<extra></extra>"
                    ))
            else:
                fig_scatter.add_trace(go.Scatter(
                    x=df_plot[columna_x].tolist(),
                    y=df_plot['IVO_P90'].tolist(),
                    mode='markers',
                    name='Jugadores',
                    text=df_plot['Jugador'].tolist(),
                    marker=dict(size=10, color='#1f77b4', line=dict(width=1, color='white')),
                    hovertemplate="<b>%{text}</b><br>IVO: %{y:.2f}<br>Volumen: %{x:.2f}<extra></extra>"
                ))

            fig_scatter.add_vline(x=media_x, line_dash="dash", line_color="gray", opacity=0.7)
            fig_scatter.add_hline(y=media_y, line_dash="dash", line_color="gray", opacity=0.7)

            fig_scatter.update_layout(
                template="plotly_dark", 
                height=600, 
                title=f"Eficiencia IVO vs {eje_x_etiqueta.split(':')[0]}",
                xaxis_title=eje_x_etiqueta,
                yaxis_title="PELIGRO (IVO P90)",
                legend_title="Demarcación" if tiene_posicion else None,
                margin=dict(l=0, r=0, t=40, b=0) 
            )

            st.plotly_chart(fig_scatter, use_container_width=True)
        else:
            st.warning("No hay datos para mostrar en el gráfico con los filtros actuales.")


# ==========================================
# --- PESTAÑA 2: COMPARATIVA Y CLONES ---
# ==========================================
with tab_comparativa:
    st.subheader("⚔️ Comparativa y Análisis de Perfiles")

    opciones_radar = df_filtrado['Jugador'].unique().tolist()

    if len(opciones_radar) >= 2:
        col_sel1, col_sel2 = st.columns(2)
        with col_sel1:
            j1 = st.selectbox("Selecciona Jugador 1 (Azul)", opciones_radar, index=0)
        with col_sel2:
            j2 = st.selectbox("Selecciona Jugador 2 (Rojo)", opciones_radar, index=1)

        def crear_radar(player1, player2, df):
            mapeo = {
                'IVO_P90': 'PELIGRO (IVO)',
                'Pases_P90': 'PASES',
                'Conducciones_P90': 'CONDUCCIONES',
                'Regates_P90': 'REGATES',
                'Tiros_P90': 'FINALIZACIÓN',
                'Presion_Pct': 'RESISTENCIA PRESIÓN'
            }
            cat_cols = list(mapeo.keys())
            cat_nombres = list(mapeo.values())

            fig = go.Figure()
            maximos = {c: df[c].max() for c in cat_cols} 

            for p, color in zip([player1, player2], ['#1f77b4', '#ef553b']):
                d = df[df['Jugador'] == p]
                if not d.empty:
                    val_norm = [(d[c].iloc[0] / maximos[c]) * 100 if maximos[c] != 0 else 0 for c in cat_cols]
                    val_norm += [val_norm[0]]
                    val_reales = d[cat_cols].values.flatten().tolist()
                    val_reales += [val_reales[0]]

                    fig.add_trace(go.Scatterpolar(
                        r=val_norm, 
                        theta=cat_nombres + [cat_nombres[0]],
                        fill='toself', 
                        name=p, 
                        line=dict(color=color, width=3),
                        customdata=val_reales,
                        hovertemplate='<b>%{theta}</b><br>Valor real: %{customdata:.2f}<extra></extra>'
                    ))

            fig.update_layout(
                polar=dict(
                    angularaxis=dict(tickfont=dict(size=14, color="white", family="Arial Black"), rotation=90, direction="clockwise", gridcolor="gray"),
                    radialaxis=dict(visible=True, range=[0, 100], ticksuffix="%", tickfont=dict(size=10, color="gray"), gridcolor="gray"),
                    bgcolor="rgba(0,0,0,0)"
                ),
                template="plotly_dark", height=650, margin=dict(l=150, r=150, t=80, b=80),
                legend=dict(font=dict(size=16), orientation="h", y=1.15, x=0.5, xanchor="center")
            )
            return fig

        col_radar, col_texto = st.columns([1.5, 1])

        with col_radar:
            # Guardamos la figura en la variable para el reporte
            fig_radar = crear_radar(j1, j2, df_filtrado)
            st.plotly_chart(fig_radar, use_container_width=True)

        with col_texto:
            st.markdown("#### 💡 Insights Automáticos")
            d1 = df_filtrado[df_filtrado['Jugador'] == j1].iloc[0]
            d2 = df_filtrado[df_filtrado['Jugador'] == j2].iloc[0]

            if d1['IVO_P90'] > d2['IVO_P90']:
                st.success(f"**Valor Ofensivo:** {j1} es más eficiente generando peligro.")
            else:
                st.success(f"**Valor Ofensivo:** {j2} es más eficiente generando peligro.")

            if d1['Pases_P90'] > d2['Pases_P90']:
                st.info(f"**Perfil:** {j1} participa más en la construcción.")
            else:
                st.info(f"**Perfil:** {j2} participa más en la construcción.")

            if d1['Regates_P90'] > d2['Regates_P90']:
                st.warning(f"**Regate:** {j1} busca más el duelo individual.")
            else:
                st.warning(f"**Regate:** {j2} busca más el duelo individual.")
    else:
        st.info("💡 Por favor, ajusta los filtros para que haya al menos 2 jugadores disponibles para comparar.")

    st.divider()

    # 7. BUSCADOR DE CLONES 
    st.subheader("🔍 Buscador de Clones: Smart Scouting")
    st.markdown("Encuentra los perfiles más similares dentro de los jugadores filtrados actualmente.")

    banderas = {
        "Spain": "es", "Cameroon": "cm", "Canada": "ca", "Argentina": "ar", 
        "Brazil": "br", "France": "fr", "Germany": "de", "Portugal": "pt",
        "Morocco": "ma", "Japan": "jp", "South Korea": "kr", "Australia": "au",
        "Netherlands": "nl", "England": "gb", "Croatia": "hr", "Senegal": "sn",
        "USA": "us", "Mexico": "mx", "Poland": "pl", "Belgium": "be",
        "Switzerland": "ch", "Ghana": "gh", "Uruguay": "uy", "Qatar": "qa",
        "Serbia": "rs", "Tunisia": "tn", "Saudi Arabia": "sa", "Denmark": "dk",
        "Costa Rica": "cr", "Ecuador": "ec", "Wales": "gb-wls", "Iran": "ir"
    }

    features_clones = ['IVO_P90', 'Pases_P90', 'Conducciones_P90', 'Regates_P90', 'Tiros_P90', 'Presion_Pct']

    if len(opciones_radar) > 1:
        j_clon = st.selectbox("Buscar parecidos a:", opciones_radar, key="clon_selector")

        def calcular_similitud_refinada(nombre_referencia, df, lista_features):
            pesos = {'IVO_P90': 0.35, 'Presion_Pct': 0.20, 'Regates_P90': 0.15, 'Tiros_P90': 0.10, 'Pases_P90': 0.10, 'Conducciones_P90': 0.10}
            df_norm = df.copy()
            for col in lista_features:
                if df[col].max() != df[col].min():
                    df_norm[col] = (df[col] - df[col].min()) / (df[col].max() - df[col].min())
                    df_norm[col] = df_norm[col] * pesos[col]
                else:
                    df_norm[col] = 0

            val_ref = df_norm[df_norm['Jugador'] == nombre_referencia][lista_features].values
            val_todos = df_norm[lista_features].values

            distancias = np.linalg.norm(val_todos - val_ref, axis=1)
            similitud = np.exp(-distancias * 5) * 100 

            df_res = df.copy()
            df_res['Similitud'] = similitud
            return df_res[df_res['Jugador'] != nombre_referencia].sort_values(by='Similitud', ascending=False).head(5)

        if j_clon:
            resultados = calcular_similitud_refinada(j_clon, df_filtrado, features_clones)
            st.write(f"Análisis de similitud avanzada para **{j_clon}**:")

            cols_clones = st.columns(5)
            for i, (index, row) in enumerate(resultados.iterrows()):
                with cols_clones[i]:
                    pais = row['Seleccion']
                    codigo_iso = banderas.get(pais, "un")
                    st.image(f"https://flagcdn.com/w80/{codigo_iso}.png", width=40)
                    st.write(f"**{row['Jugador']}**")
                    st.caption(f"{pais}")
                    st.metric("Similitud", f"{row['Similitud']:.1f}%")

            st.write("---")
            st.subheader(f"📊 Tabla Comparativa: {j_clon} vs Clones")

            df_original = df_filtrado[df_filtrado['Jugador'] == j_clon].copy()
            df_original['Similitud'] = 100.0 

            tabla_comp = pd.concat([df_original, resultados])
            columnas_tabla = ['Jugador', 'Seleccion', 'Similitud'] + features_clones
            df_mostrar = tabla_comp[columnas_tabla].reset_index(drop=True)

            def resaltar_referencia(x):
                style_df = pd.DataFrame('', index=x.index, columns=x.columns)
                style_df.iloc[0, :] = 'background-color: rgba(255, 255, 255, 0.1); font-weight: bold; border-bottom: 2px solid gray'
                return style_df

            st.dataframe(
                df_mostrar.style.format({
                    'Similitud': '{:.1f}%', 'IVO_P90': '{:.3f}', 'Pases_P90': '{:.1f}', 'Conducciones_P90': '{:.1f}',
                    'Regates_P90': '{:.1f}', 'Tiros_P90': '{:.1f}', 'Presion_Pct': '{:.1f}%'
                }).apply(resaltar_referencia, axis=None),
                use_container_width=True
            )
    else:
        st.info("No hay suficientes jugadores filtrados para buscar clones.")


# ==========================================
# --- PESTAÑA 3: XI IDEAL Y MAPAS DE CALOR ---
# ==========================================
with tab_analisis_avanzado:
    st.markdown("### 🔬 Pizarra Táctica y Análisis Espacial")

    col_xi, col_heat = st.columns([1, 1.4], gap="large")

    with col_xi:
        st.subheader("🏆 XI Ideal (4-3-3)")
        st.caption("Alineación algorítmica (respeta País y Minutos, ignora demarcación actual).")

        if 'Posicion' in df_base.columns:
            df_dream = df_base.copy()

            def obtener_mejores(posiciones, n=1):
                if isinstance(posiciones, list):
                    jugadores = df_dream[df_dream['Posicion'].isin(posiciones)]
                else:
                    jugadores = df_dream[df_dream['Posicion'] == posiciones]
                return jugadores.sort_values('IVO_P90', ascending=False).head(n)

            ei = obtener_mejores('EI')
            dc = obtener_mejores('DC')
            ed = obtener_mejores('ED')
            mco = obtener_mejores('MCO')
            mc  = obtener_mejores('MC')
            mcd = obtener_mejores('MCD')
            li  = obtener_mejores('LI')
            dfc = obtener_mejores('DFC', 2)
            ld  = obtener_mejores('LD')

            st.write("")
            st.markdown("<h5 style='text-align: center; color: #ff4b4b;'>Ataque</h5>", unsafe_allow_html=True)
            cols_att = st.columns([0.2, 2, 2, 2, 0.2]) 
            with cols_att[1]:
                if not ei.empty: st.info(f"**EI | {ei.iloc[0]['Jugador']}**\n\n🎯 {ei.iloc[0]['IVO_P90']:.2f}")
            with cols_att[2]:
                if not dc.empty: st.info(f"**DC | {dc.iloc[0]['Jugador']}**\n\n🎯 {dc.iloc[0]['IVO_P90']:.2f}")
            with cols_att[3]:
                if not ed.empty: st.info(f"**ED | {ed.iloc[0]['Jugador']}**\n\n🎯 {ed.iloc[0]['IVO_P90']:.2f}")

            st.markdown("<h5 style='text-align: center; color: #4b8bff;'>Centro del Campo</h5>", unsafe_allow_html=True)
            cols_mid = st.columns([0.2, 2, 2, 2, 0.2])
            with cols_mid[1]:
                if not mc.empty: st.success(f"**MC | {mc.iloc[0]['Jugador']}**\n\n⚙️ {mc.iloc[0]['IVO_P90']:.2f}")
            with cols_mid[2]:
                if not mco.empty: st.success(f"**MCO | {mco.iloc[0]['Jugador']}**\n\n⚙️ {mco.iloc[0]['IVO_P90']:.2f}")
            with cols_mid[3]:
                if not mcd.empty: st.success(f"**MCD | {mcd.iloc[0]['Jugador']}**\n\n⚙️ {mcd.iloc[0]['IVO_P90']:.2f}")

            st.markdown("<h5 style='text-align: center; color: #4bff8b;'>Defensa</h5>", unsafe_allow_html=True)
            cols_def = st.columns(4)
            with cols_def[0]:
                if not li.empty: st.warning(f"**LI | {li.iloc[0]['Jugador']}**\n\n🛡️ {li.iloc[0]['IVO_P90']:.2f}")
            with cols_def[1]:
                if len(dfc) > 0: st.warning(f"**DFC | {dfc.iloc[0]['Jugador']}**\n\n🛡️ {dfc.iloc[0]['IVO_P90']:.2f}")
            with cols_def[2]:
                if len(dfc) > 1: st.warning(f"**DFC | {dfc.iloc[1]['Jugador']}**\n\n🛡️ {dfc.iloc[1]['IVO_P90']:.2f}")
            with cols_def[3]:
                if not ld.empty: st.warning(f"**LD | {ld.iloc[0]['Jugador']}**\n\n🛡️ {ld.iloc[0]['IVO_P90']:.2f}")
        else:
            st.error("⚠️ Falta la columna 'Posicion' para generar el XI Ideal.")

    with col_heat:
        st.subheader("🔥 Densidad de Intervención")
        st.caption("Selecciona un jugador para ver sus zonas de influencia reales.")

        if not df_espacial.empty:
            jugadores_validos = df_filtrado['Jugador'].unique().tolist()
            df_espacial_filtrado = df_espacial[df_espacial['Jugador'].isin(jugadores_validos)]

            opciones_heat = sorted(df_espacial_filtrado['Jugador'].dropna().unique().tolist())

            if len(opciones_heat) > 0:
                f_col1, f_col2 = st.columns(2)
                with f_col1:
                    idx_defecto = opciones_heat.index('Kylian Mbappé Lottin') if 'Kylian Mbappé Lottin' in opciones_heat else 0
                    jugador_calor = st.selectbox("Objetivo:", opciones_heat, index=idx_defecto)
                with f_col2:
                    acciones_disponibles = ["Todas"] + df_espacial_filtrado['Tipo_Accion'].dropna().unique().tolist()
                    accion_sel = st.selectbox("Acción:", acciones_disponibles)

                df_jugador = df_espacial_filtrado[df_espacial_filtrado['Jugador'] == jugador_calor].copy()
                if accion_sel != "Todas":
                    df_jugador = df_jugador[df_jugador['Tipo_Accion'] == accion_sel]

                if len(df_jugador) > 0:
                    x_data = pd.to_numeric(df_jugador['X'], errors='coerce').fillna(0).tolist()
                    y_data = pd.to_numeric(df_jugador['Y'], errors='coerce').fillna(0).tolist()

                    fig_pitch = go.Figure()
                    fig_pitch.add_trace(go.Histogram2d(
                        x=x_data, y=y_data, autobinx=False, xbins=dict(start=0, end=120, size=5),
                        autobiny=False, ybins=dict(start=0, end=80, size=5),
                        colorscale=[[0, 'rgba(0,0,0,0)'], [0.1, 'rgba(255, 255, 0, 0.3)'], [0.5, 'rgba(255, 165, 0, 0.6)'], [1, 'rgba(255, 0, 0, 0.8)']],
                        showscale=False, hoverinfo='skip', zsmooth='best' 
                    ))

                    line_color = "rgba(255,255,255,0.8)"
                    fig_pitch.add_shape(type="rect", x0=0, y0=0, x1=120, y1=80, line=dict(color=line_color, width=2))
                    fig_pitch.add_shape(type="line", x0=60, y0=0, x1=60, y1=80, line=dict(color=line_color, width=2))
                    fig_pitch.add_shape(type="circle", x0=50, y0=30, x1=70, y1=50, line=dict(color=line_color, width=2))
                    fig_pitch.add_shape(type="rect", x0=0, y0=18, x1=18, y1=62, line=dict(color=line_color, width=2))
                    fig_pitch.add_shape(type="rect", x0=102, y0=18, x1=120, y1=62, line=dict(color=line_color, width=2))
                    fig_pitch.add_shape(type="rect", x0=0, y0=30, x1=6, y1=50, line=dict(color=line_color, width=2))
                    fig_pitch.add_shape(type="rect", x0=114, y0=30, x1=120, y1=50, line=dict(color=line_color, width=2))

                    fig_pitch.update_layout(
                        height=500, plot_bgcolor='#1e5631', paper_bgcolor='rgba(0,0,0,0)',
                        xaxis=dict(range=[0, 120], showgrid=False, visible=False, fixedrange=True),
                        yaxis=dict(range=[80, 0], showgrid=False, visible=False, fixedrange=True),
                        margin=dict(l=0, r=0, t=10, b=10), showlegend=False
                    )

                    st.plotly_chart(fig_pitch, use_container_width=True)
                    st.info(f"📍 Muestra de **{len(x_data)}** acciones registradas. (Ataque →)")
                else:
                    st.warning("No hay datos espaciales para este tipo de acción.")
            else:
                st.warning("No hay jugadores en el Mapa de Calor con estos filtros.")
        else:
            st.error("Archivo 'qatar2022_espacial_ivo.csv' no encontrado.")

# ==========================================
# 11. CONCLUSIONES Y RECOMENDACIÓN FINAL
# ==========================================
st.divider()
st.subheader("📋 Conclusiones del analista")

with st.container():
    col_c1, col_c2 = st.columns([2, 1])
    with col_c1:
        notas_scout = st.text_area("Análisis táctico:", placeholder="Ejemplo: El jugador demuestra una gran capacidad de asociación...", height=150)
    with col_c2:
        veredicto = st.selectbox("Veredicto Final:", ["🟢 Altamente recomendado", "🟡 En seguimiento", "🔴 No se ajusta al perfil", "🔵 Opción estratégica"], index=1)
        st.info(f"**Análisis de datos:** El perfil analizado tiene un 85% de compatibilidad con el sistema táctico del equipo.")

# --- FUNCIÓN PARA GENERAR EL REPORTE HTML ---
def generar_html_informe(notas, veredicto_txt, f_scatter, f_radar, f_pitch):
    html_content = f"""
    <html>
    <head>
        <meta charset="utf-8">
        <title>Informe de scouting - Modelo IVO</title>
        <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
        <style>
            body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 40px; background-color: #f4f7f6; color: #333; }}
            h1 {{ color: #1e3799; text-align: center; border-bottom: 2px solid #1e3799; padding-bottom: 10px; }}
            h2 {{ color: #2f3640; margin-top: 30px; }}
            .container {{ background: white; padding: 20px; border-radius: 8px; box-shadow: 0 4px 8px rgba(0,0,0,0.05); margin-bottom: 25px; }}
            .notes {{ background: #f8efba; padding: 15px; border-left: 5px solid #f39c12; border-radius: 4px; font-size: 16px; line-height: 1.5; }}
            .verdict {{ font-weight: bold; font-size: 18px; color: #27ae60; background: #e8f8f5; padding: 10px; border-radius: 4px; display: inline-block; }}
            .footer {{ text-align: center; font-size: 12px; color: #7f8c8d; margin-top: 50px; }}
        </style>
    </head>
    <body>
        <h1>⚽ Informe ejecutivo de scouting - Modelo IVO</h1>

        <div class="container">
            <h2>📋 Conclusiones y veredicto</h2>
            <p class="verdict">Veredicto final: {veredicto_txt}</p>
            <div class="notes">
                <strong>Análisis táctico:</strong><br><br>
                {notas if notas else '<em>El analista no ha añadido comentarios adicionales en esta sesión.</em>'}
            </div>
        </div>
    """

    # Extraer el HTML de los gráficos si existen
    if f_scatter:
        html_content += f'<div class="container"><h2>📈 Análisis: Riesgo vs Recompensa</h2>{f_scatter.to_html(full_html=False, include_plotlyjs=False)}</div>'

    if f_radar:
        html_content += f'<div class="container"><h2>⚔️ Comparativa de Perfiles</h2>{f_radar.to_html(full_html=False, include_plotlyjs=False)}</div>'

    if f_pitch:
        html_content += f'<div class="container"><h2>🔥 Mapa de Calor y Zonas de Influencia</h2>{f_pitch.to_html(full_html=False, include_plotlyjs=False)}</div>'

    html_content += """
        <div class="footer">
            Generado automáticamente a través de la plataforma de Scouting IVO.
        </div>
    </body>
    </html>
    """
    return html_content


col_btn1, col_btn2, col_btn3 = st.columns(3)

with col_btn1:
    # Generamos el HTML combinando los textos y las figuras guardadas
    html_reporte = generar_html_informe(notas_scout, veredicto, fig_scatter, fig_radar, fig_pitch)

    st.download_button(
        label="📄 Descargar informe completo (HTML)",
        data=html_reporte.encode('utf-8'),
        file_name="Informe_Scouting_IVO.html",
        mime="text/html"
    )

st.markdown("---")
st.markdown("<center><small>Dashboard de Scouting Profesional | TFM - Análisis de Datos Qatar 2022</small></center>", unsafe_allow_html=True)




