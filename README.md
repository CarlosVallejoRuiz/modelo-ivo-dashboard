# ⚽ Dashboard de Scouting Profesional: Modelo IVO (Qatar 2022)

**Trabajo de Fin de Máster (TFM) - Juan Carlos Vallejo Ruiz**

![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white)
![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Plotly](https://img.shields.io/badge/Plotly-3F4F75?style=for-the-badge&logo=plotly&logoColor=white)
![StatsBomb](https://img.shields.io/badge/Data-StatsBomb-red?style=for-the-badge)

## 📌 Sobre el Proyecto
Este repositorio contiene el código fuente de una herramienta interactiva de Scouting Deportivo. La aplicación permite evaluar, comparar y descubrir perfiles de futbolistas basándose en el **Índice de Valor Ofensivo (IVO)**, una métrica algorítmica propia diseñada para medir la eficiencia real en la generación de peligro.

El análisis se ha realizado procesando los eventos del Mundial de Qatar 2022 extraídos de la API de **StatsBomb Open Data**.

## 🚀 Funcionalidades Principales
La herramienta está estructurada en tres niveles de análisis táctico y estadístico:

1. **📊 Exploración y Mercado:** - Ranking interactivo filtrable por minutos, selección y demarcación.
   - **Matriz de Cuadrantes (Riesgo vs Recompensa):** Identificación visual de *outliers* tácticos (jugadores con alto volumen de intervención y alta eficiencia).
2. **⚔️ Scouting Individual y Comparativa:**
   - **Radares de Rendimiento:** Cara a cara entre dos perfiles normalizado al percentil máximo del torneo.
   - **Buscador de Clones:** Algoritmo basado en **Distancia Euclidiana Ponderada** que encuentra los 5 perfiles más similares del torneo basándose en el estilo de juego (IVO, Pases, Conducciones, Regates y Resistencia a la Presión).
3. **🔬 Análisis Táctico Espacial:**
   - **XI Ideal Dinámico:** Generación automática del mejor once posicional (1-4-3-3) que respeta los filtros activos.
   - **Mapas de Calor (Densidad de Intervención):** Renderizado espacial de las zonas de influencia reales de cada jugador sobre el terreno de juego.

## 🛠️ Tecnologías Utilizadas
- **Análisis de Datos:** `pandas`, `numpy`
- **Visualización:** `plotly` (Radar Charts, Heatmaps 2D, Scatter Plots)
- **Despliegue Web:** `streamlit`

## 💻 Instalación y Uso Local
Si deseas ejecutar este dashboard en tu propia máquina:

1. Clona el repositorio:
   ```bash
   git clone [https://github.com/tu-usuario/nombre-de-tu-repo.git](https://github.com/tu-usuario/nombre-de-tu-repo.git)
