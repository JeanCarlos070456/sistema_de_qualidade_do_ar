from datetime import datetime

import streamlit as st

from charts import build_reference_table, chart_co2, chart_means, chart_statistics
from data_loader import build_statistics, filter_data, load_data
from map_export import export_static_map
from map_view import render_map
from report import export_plotly_figures, generate_pdf
from rules import cor_classificacao
from settings import APP_TITLE, PAGE_TITLE
from ui import render_sidebar


st.set_page_config(layout="wide", page_title=PAGE_TITLE)
st.markdown(f"<h2>{APP_TITLE}</h2>", unsafe_allow_html=True)


def main():
    try:
        df = load_data()
    except Exception as e:
        st.error(f"Erro ao carregar dados: {e}")
        st.stop()

    controls = render_sidebar(df)

    df_filtrado = filter_data(
        df=df,
        data_sel=controls["data_sel"],
        pontos_sel=controls["pontos_sel"],
        hora_sel=controls["hora_sel"],
    )

    if df_filtrado.empty:
        st.warning("Nenhum dado encontrado para os filtros selecionados.")
        st.stop()

    st.markdown("### Tabela de Coletas Filtradas")
    tabela_exibir = df_filtrado[
        [
            "pontos",
            "DataHora",
            "Temperatura (°C)",
            "Classificação Temp",
            "RH (%)",
            "Classificação RH",
            "CO2 (ppm)",
            "Classificação CO2",
            "Ponto de Orvalho (°C)",
        ]
    ].copy()

    styled_df = tabela_exibir.style.applymap(
        cor_classificacao,
        subset=["Classificação Temp", "Classificação RH", "Classificação CO2"],
    )
    st.dataframe(styled_df, use_container_width=True)

    estat = build_statistics(df_filtrado, controls["col_sel"])

    tabela_ref = build_reference_table(
        controls["ext_temp"],
        controls["ext_ur"],
        controls["ext_co2"],
    )

    st.markdown("### Referências usadas (Interno × Externo)")
    st.dataframe(tabela_ref, use_container_width=True)

    fig_stats = chart_statistics(
        estat=estat,
        variavel=controls["variavel"],
        data_sel=controls["data_sel"],
    )
    st.plotly_chart(fig_stats, use_container_width=True)

    fig_co2 = chart_co2(
        df_filtrado=df_filtrado,
        ref_tipo=controls["ref_tipo"],
        ext_co2=controls["ext_co2"],
    )
    st.plotly_chart(fig_co2, use_container_width=True)

    fig_temp, fig_umid, fig_co2_ref = chart_means(
        df_filtrado=df_filtrado,
        ref_tipo=controls["ref_tipo"],
        ext_temp=controls["ext_temp"],
        ext_ur=controls["ext_ur"],
        ext_co2=controls["ext_co2"],
    )
    st.plotly_chart(fig_temp, use_container_width=True)
    st.plotly_chart(fig_umid, use_container_width=True)
    st.plotly_chart(fig_co2_ref, use_container_width=True)

    st.markdown("### Mapa dos pontos de coleta")
    render_map(
        df_filtrado=df_filtrado,
        col_sel=controls["col_sel"],
        variavel=controls["variavel"],
        pontos_sel=controls["pontos_sel"],
    )

    st.markdown("---")
    st.subheader("📄 Exportar relatório (PDF)")

    if st.button("Gerar PDF com Tabela, Gráficos e Mapa"):
        temp_dir_graficos = None
        temp_dir_mapa = None

        try:
            temp_dir_graficos, png_paths = export_plotly_figures(
                fig_temp=fig_temp,
                fig_umid=fig_umid,
                fig_co2=fig_co2_ref,
            )

            temp_dir_mapa, mapa_path = export_static_map(
                df_filtrado=df_filtrado,
                pontos_sel=controls["pontos_sel"],
                col_sel=controls["col_sel"],
                variavel=controls["variavel"],
            )

            pdf_buffer = generate_pdf(
                tabela_ref_df=tabela_ref,
                png_paths=png_paths,
                data_sel=controls["data_sel"],
                pontos_sel=controls["pontos_sel"],
                mapa_path=mapa_path,
            )

            st.download_button(
                label="⬇️ Baixar relatório (PDF)",
                data=pdf_buffer,
                file_name=f"relatorio_qualidade_ar_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf",
                mime="application/pdf",
            )

        except Exception as e:
            st.error(f"Não foi possível gerar o PDF: {e}")

        finally:
            if temp_dir_graficos is not None:
                temp_dir_graficos.cleanup()
            if temp_dir_mapa is not None:
                temp_dir_mapa.cleanup()


if __name__ == "__main__":
    main()