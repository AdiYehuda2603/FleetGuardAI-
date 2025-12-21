# -*- coding: utf-8 -*-
"""
Enhanced Data Table Component
Provides professional data table presentation with filtering, sorting, and heatmap styling
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from typing import Optional, List, Dict, Any


def format_currency(value):
    """Format currency values in Hebrew style"""
    try:
        return f"₪{value:,.2f}"
    except:
        return str(value)


def format_number(value):
    """Format numbers with thousands separator"""
    try:
        return f"{value:,}"
    except:
        return str(value)


def get_color_scale(value, min_val, max_val, inverse=False):
    """
    Generate color based on value position in range
    inverse=True means lower is better (green), higher is worse (red)
    """
    # Handle NA values
    if pd.isna(value) or pd.isna(min_val) or pd.isna(max_val):
        return 'background-color: #f0f2f6'

    # Convert to numeric, return neutral color if conversion fails
    try:
        value = float(value)
        min_val = float(min_val)
        max_val = float(max_val)
    except (ValueError, TypeError):
        return 'background-color: #f0f2f6'

    # Handle equal min/max
    if min_val == max_val:
        return 'background-color: #f0f2f6'

    normalized = (value - min_val) / (max_val - min_val)

    if inverse:
        # Lower is better: green -> yellow -> red
        if normalized < 0.33:
            intensity = int(240 - (normalized * 3 * 60))
            return f'background-color: rgb(200, {intensity}, 200)'
        elif normalized < 0.66:
            intensity = int(240 - ((normalized - 0.33) * 3 * 60))
            return f'background-color: rgb({intensity}, {intensity}, 150)'
        else:
            intensity = int(240 - ((normalized - 0.66) * 3 * 60))
            return f'background-color: rgb(255, {intensity}, {intensity})'
    else:
        # Higher is better: red -> yellow -> green
        if normalized < 0.33:
            intensity = int(180 + (normalized * 3 * 40))
            return f'background-color: rgb(255, {intensity}, {intensity})'
        elif normalized < 0.66:
            intensity = int(220 + ((normalized - 0.33) * 3 * 20))
            return f'background-color: rgb({intensity}, {intensity}, 150)'
        else:
            intensity = int(200 + ((normalized - 0.66) * 3 * 40))
            return f'background-color: rgb(200, {intensity}, 200)'


def render_enhanced_dataframe(
    df: pd.DataFrame,
    title: str = "",
    key_prefix: str = "table",
    enable_search: bool = True,
    enable_sorting: bool = True,
    enable_heatmap: bool = False,
    heatmap_columns: Optional[List[str]] = None,
    currency_columns: Optional[List[str]] = None,
    number_columns: Optional[List[str]] = None,
    page_size: int = 25,
    height: int = 600,
    show_summary: bool = True
):
    """
    Render an enhanced, professional data table with advanced features

    Args:
        df: DataFrame to display
        title: Table title
        key_prefix: Unique prefix for widget keys
        enable_search: Enable text search across all columns
        enable_sorting: Enable column sorting
        enable_heatmap: Apply heatmap coloring to numeric columns
        heatmap_columns: Specific columns for heatmap (if None, applies to all numeric)
        currency_columns: Columns to format as currency
        number_columns: Columns to format with thousand separators
        page_size: Rows per page
        height: Table height in pixels
        show_summary: Show summary statistics
    """

    if df.empty:
        st.warning("⚠️ אין נתונים להצגה")
        return

    # Create a copy to avoid modifying original
    display_df = df.copy()

    # Header section
    if title:
        st.subheader(title)

    col1, col2, col3 = st.columns([2, 1, 1])

    with col1:
        if enable_search:
            search_term = st.text_input(
                "🔍 חיפוש",
                placeholder="הקלד טקסט לחיפוש...",
                key=f"{key_prefix}_search"
            )
            if search_term:
                # Search across all string columns
                mask = display_df.astype(str).apply(
                    lambda row: row.str.contains(search_term, case=False, na=False).any(),
                    axis=1
                )
                display_df = display_df[mask]
                st.caption(f"📊 נמצאו {len(display_df)} תוצאות")

    with col2:
        if enable_sorting and not display_df.empty:
            sort_column = st.selectbox(
                "📊 מיון לפי",
                options=["ללא"] + list(display_df.columns),
                key=f"{key_prefix}_sort"
            )
            if sort_column != "ללא":
                sort_order = st.radio(
                    "",
                    options=["עולה ⬆", "יורד ⬇"],
                    horizontal=True,
                    key=f"{key_prefix}_order"
                )
                ascending = (sort_order == "עולה ⬆")
                display_df = display_df.sort_values(by=sort_column, ascending=ascending)

    with col3:
        # Export options
        if not display_df.empty:
            st.download_button(
                label="📥 ייצא CSV",
                data=display_df.to_csv(index=False).encode('utf-8-sig'),
                file_name=f"{key_prefix}_export.csv",
                mime="text/csv",
                key=f"{key_prefix}_export"
            )

    st.markdown("---")

    # Summary statistics
    if show_summary and not display_df.empty:
        summary_cols = st.columns(4)

        with summary_cols[0]:
            st.metric("📊 סה\"כ שורות", len(display_df))

        with summary_cols[1]:
            st.metric("📋 עמודות", len(display_df.columns))

        # Try to show meaningful stats
        numeric_cols = display_df.select_dtypes(include=['number']).columns

        if len(numeric_cols) > 0:
            first_numeric = numeric_cols[0]

            with summary_cols[2]:
                avg_val = display_df[first_numeric].mean()
                label = f"ממוצע {first_numeric}"
                if currency_columns and first_numeric in currency_columns:
                    st.metric(label, format_currency(avg_val))
                else:
                    st.metric(label, f"{avg_val:,.2f}")

            with summary_cols[3]:
                sum_val = display_df[first_numeric].sum()
                label = f"סה\"כ {first_numeric}"
                if currency_columns and first_numeric in currency_columns:
                    st.metric(label, format_currency(sum_val))
                else:
                    st.metric(label, f"{sum_val:,.2f}")

        st.markdown("---")

    # Apply formatting
    styled_df = display_df.copy()

    # Format currency columns
    if currency_columns:
        for col in currency_columns:
            if col in styled_df.columns:
                styled_df[col] = styled_df[col].apply(format_currency)

    # Format number columns
    if number_columns:
        for col in number_columns:
            if col in styled_df.columns:
                styled_df[col] = styled_df[col].apply(format_number)

    # Apply heatmap styling if enabled
    if enable_heatmap:
        # Determine which columns to apply heatmap to
        if heatmap_columns is None:
            heatmap_columns = display_df.select_dtypes(include=['number']).columns.tolist()

        # Convert heatmap columns to numeric (handle strings from database)
        for col in heatmap_columns:
            if col in display_df.columns:
                display_df[col] = pd.to_numeric(display_df[col], errors='coerce')

        # Create style function
        def apply_heatmap(row):
            styles = []
            for col in display_df.columns:
                if col in heatmap_columns and col in display_df.select_dtypes(include=['number']).columns:
                    try:
                        min_val = display_df[col].min()
                        max_val = display_df[col].max()
                        value = row[col]

                        # Determine if lower is better (cost-related columns)
                        inverse = any(keyword in col.lower() for keyword in ['cost', 'עלות', 'total', 'סה"כ'])

                        styles.append(get_color_scale(value, min_val, max_val, inverse=inverse))
                    except:
                        styles.append('')
                else:
                    styles.append('')
            return styles

        # Apply styling
        styled_display = styled_df.style.apply(apply_heatmap, axis=1)

        # Display with st.dataframe
        st.dataframe(
            styled_display,
            use_container_width=True,
            height=height
        )
    else:
        # Display regular dataframe
        st.dataframe(
            styled_df,
            use_container_width=True,
            height=height
        )

    # Pagination info
    st.caption(f"📄 מציג {min(page_size, len(display_df))} מתוך {len(display_df)} שורות")


def render_data_table_tabs(db):
    """
    Render the enhanced data tables in multiple tabs
    Replaces the old Tab 5 (Raw Data) implementation
    """

    st.header("📋 מאגר הנתונים המלא")
    st.caption("כלי מתקדם לניתוח וחיפוש נתונים עם תצוגות ממוקדות")

    # Create tabs
    subtab1, subtab2, subtab3, subtab4, subtab5 = st.tabs([
        "📊 תצוגה מלאה (מאוחדת)",
        "🧾 חשבוניות",
        "📝 שורות חשבונית",
        "🚗 רכבים",
        "📧 היסטוריית אימייל"
    ])

    # Tab 1: Full joined view
    with subtab1:
        try:
            # Get full joined data
            df_full = db.get_full_view()

            if not df_full.empty:
                render_enhanced_dataframe(
                    df=df_full,
                    title="תצוגה מאוחדת - חשבוניות + שורות + רכבים",
                    key_prefix="full_data",
                    enable_search=True,
                    enable_sorting=True,
                    enable_heatmap=True,
                    currency_columns=['subtotal', 'vat', 'total', 'unit_price', 'line_total'],
                    number_columns=['odometer_km', 'qty'],
                    show_summary=True
                )
            else:
                st.info("ℹ️ אין נתונים להצגה. אנא הוסף חשבוניות במערכת.")
        except Exception as e:
            st.error(f"❌ שגיאה בטעינת נתונים: {str(e)}")

    # Tab 2: Invoices only
    with subtab2:
        try:
            df_invoices = db.get_all_invoices()

            if not df_invoices.empty:
                render_enhanced_dataframe(
                    df=df_invoices,
                    title="חשבוניות",
                    key_prefix="invoices",
                    enable_search=True,
                    enable_sorting=True,
                    enable_heatmap=True,
                    heatmap_columns=['subtotal', 'vat', 'total', 'odometer_km'],
                    currency_columns=['subtotal', 'vat', 'total'],
                    number_columns=['odometer_km'],
                    show_summary=True
                )
            else:
                st.info("ℹ️ אין חשבוניות במערכת")
        except Exception as e:
            st.error(f"❌ שגיאה: {str(e)}")

    # Tab 3: Invoice lines
    with subtab3:
        try:
            df_lines = db.get_invoice_lines()

            if not df_lines.empty:
                render_enhanced_dataframe(
                    df=df_lines,
                    title="שורות חשבונית מפורטות",
                    key_prefix="invoice_lines",
                    enable_search=True,
                    enable_sorting=True,
                    enable_heatmap=True,
                    heatmap_columns=['qty', 'unit_price', 'line_total'],
                    currency_columns=['unit_price', 'line_total'],
                    number_columns=['qty'],
                    show_summary=True
                )
            else:
                st.info("ℹ️ אין שורות חשבונית")
        except Exception as e:
            st.error(f"❌ שגיאה: {str(e)}")

    # Tab 4: Vehicles
    with subtab4:
        try:
            df_vehicles = db.get_all_vehicles()

            if not df_vehicles.empty:
                render_enhanced_dataframe(
                    df=df_vehicles,
                    title="רכבים בצי",
                    key_prefix="vehicles",
                    enable_search=True,
                    enable_sorting=True,
                    enable_heatmap=False,  # Vehicles don't need heatmap
                    number_columns=['initial_km', 'year'],
                    show_summary=True
                )
            else:
                st.info("ℹ️ אין רכבים במערכת")
        except Exception as e:
            st.error(f"❌ שגיאה: {str(e)}")

    # Tab 5: Email sync history
    with subtab5:
        try:
            df_email = db.get_email_sync_history(limit=100)

            if not df_email.empty:
                # Rename columns to Hebrew
                df_email_display = df_email.copy()
                df_email_display.columns = [
                    'ID', 'מזהה מייל', 'נושא', 'שולח',
                    'תאריך קבלה', 'תאריך עיבוד', 'חשבוניות', 'סטטוס'
                ]

                render_enhanced_dataframe(
                    df=df_email_display,
                    title="היסטוריית סנכרון אימייל",
                    key_prefix="email_history",
                    enable_search=True,
                    enable_sorting=True,
                    enable_heatmap=False,
                    show_summary=True
                )
            else:
                st.info("ℹ️ אין היסטוריית סנכרון")
        except Exception as e:
            st.error(f"❌ שגיאה: {str(e)}")
