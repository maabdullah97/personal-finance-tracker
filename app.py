
import streamlit as st
from datetime import date
from decimal import Decimal
import pandas as pd
from database import (
    create_tables,
    add_transaction,
    get_transactions,
    get_balance_summary,
    seed_default_categories,
    add_category,
    get_categories,
    rename_category,
    delete_category,
    delete_transaction,
    update_transaction,
)



# Configure the application
st.set_page_config(
    page_title="Personal Finance Tracker",
    page_icon="💷",
    layout="wide",
)

# Initialise database
create_tables()
seed_default_categories()

def format_money(pence):
    """Convert pence into formatted GBP."""
    return f"£{pence / 100:,.2f}"


# Page heading
st.title("💷 Personal Finance Tracker")
st.caption("Your money, clearly managed.")

# Retrieve financial totals
income, expenses, balance = get_balance_summary()

st.divider()

# Dashboard summary
col1, col2, col3 = st.columns(3)

with col1:
    st.metric("Total Income", format_money(income))

with col2:
    st.metric("Total Expenses", format_money(expenses))

with col3:
    st.metric("Available Balance", format_money(balance))

st.divider()

# Add a transaction
st.subheader("Add a Transaction")

with st.form("transaction_form", clear_on_submit=True):

    transaction_type = st.selectbox(
        "Transaction Type",
        ["Expense", "Income"],
    )

    # Show categories matching the transaction type
    available_categories = get_categories(transaction_type)

    category_options = {
        category[1]: category[0]
        for category in available_categories
    }

    selected_category = st.selectbox(
        "Category",
        options=list(category_options.keys()),
        placeholder="Select a category",
    )

    selected_category_id = category_options.get(
        selected_category
    )

    description = st.text_input(
        "Description",
        placeholder="e.g. Monthly Salary or Groceries",
    )

    amount = st.number_input(
        "Amount (£)",
        min_value=0.01,
        value=10.00,
        step=1.00,
        format="%.2f",
    )

    transaction_date = st.date_input(
        "Date",
        value=date.today(),
        format="DD/MM/YYYY",
    )

    submitted = st.form_submit_button(
        "Save Transaction",
        use_container_width=True,
    )

    if submitted:
        if not description.strip():
            st.error("Please enter a description.")
        else:
            amount_pence = int(
                Decimal(str(amount)) * 100
            )

            

            add_transaction(
                description.strip(),
                amount_pence,
                transaction_type,
                transaction_date.isoformat(),
                category_id=selected_category_id,
            )

            st.success("Transaction saved successfully!")
            st.rerun()


st.divider()

# Transaction history
st.subheader("Transaction History")

transactions = get_transactions()

if transactions:
    table_data = []

    for transaction in transactions:
        transaction_id, desc, amount_pence, t_type, t_date, category_name = transaction

        table_data.append({
            "Date": date.fromisoformat(t_date).strftime("%d/%m/%Y"),
            "Description": desc,
            "Category": category_name,
            "Type": t_type,
            "Amount": (
                f"+{format_money(amount_pence)}"
                if t_type == "Income"
                else f"-{format_money(amount_pence)}"
            ),
        })

    st.dataframe(
        table_data,
        use_container_width=True,
        hide_index=True,
    )


    
    st.subheader("Edit a Transaction")

    edit_options = {
        f"{t[4]} | {t[1]} | £{t[2] / 100:,.2f} | ID: {t[0]}": t
        for t in transactions
    }

    selected_edit = st.selectbox(
        "Select a transaction to edit",
        options=list(edit_options.keys()),
    )

    selected_transaction_id = edit_options[selected_edit][0]

    
    transaction_to_edit = next(
        (t for t in transactions if str(t[0]) == str(selected_transaction_id)),
        None
    )

    
    if transaction_to_edit:
        edit_description = st.text_input(
            "Edit Description",
            value=transaction_to_edit[1],
            key=f"edit_description_{selected_transaction_id}"
        )

        edit_amount = st.number_input(
            "Edit Amount (£)",
            min_value=0.01,
            value=transaction_to_edit[2] / 100,
            step=1.00,
            format="%.2f",
            key=f"edit_amount_{selected_transaction_id}"
        )

        edit_type = st.selectbox(
            "Edit Transaction Type",
            options=["Income", "Expense"],
            index=["Income", "Expense"].index(transaction_to_edit[3]),
            key=f"edit_type_{selected_transaction_id}"
        )

        edit_date = st.date_input(
            "Edit Transaction Date",
            value=date.fromisoformat(transaction_to_edit[4]),
            key=f"edit_date_{selected_transaction_id}"
        )

        edit_category_options = {
            category[1]: category[0]
            for category in get_categories()
            if category[2] == edit_type
        }

        edit_category_names = ["Uncategorised"] + list(edit_category_options.keys())

        edit_category = st.selectbox(
            "Edit Transaction Category",
            options=edit_category_names,
            key=f"edit_category_{selected_transaction_id}"
        )

        if st.button("Save Transaction Changes", type="primary"):
            category_id = edit_category_options.get(edit_category)

            success = update_transaction(
                selected_transaction_id,
                edit_description,
                round(edit_amount * 100),
                edit_type,
                edit_date.isoformat(),
                category_id
            )

            if success:
                st.success("Transaction updated successfully!")
                st.rerun()
            else:
                st.error("Unable to update transaction.")

    
    st.subheader("Delete a Transaction")

    transaction_options = {
        f"{t[4]} | {t[1]} | £{t[2] / 100:,.2f} | ID: {t[0]}": t[0]
        for t in transactions
    }

    selected_transaction = st.selectbox(
        "Select a transaction to delete",
        options=list(transaction_options.keys()),
    )


    confirm_delete = st.checkbox(
        "I confirm that I want to permanently delete this transaction."
    )

    if st.button("Delete Selected Transaction", type="primary"):
        if confirm_delete:
            transaction_id = transaction_options[selected_transaction]

            if delete_transaction(transaction_id):
                st.success("Transaction deleted successfully!")
                st.rerun()
            else:
                st.error("Unable to delete this transaction.")
        else:
            st.warning("Please tick the confirmation box first.")


else:
    st.info("No transactions yet. Add your first income or expense above.")



# Category management
st.divider()
st.subheader("Manage Categories")

with st.expander("Add, Rename or Delete Categories"):

    st.markdown("#### Add a New Category")

    with st.form("add_category_form", clear_on_submit=True):
        new_category_name = st.text_input(
            "Category Name",
            placeholder="e.g. Coffee, Holidays, Investments",
        )

        new_category_type = st.selectbox(
            "Category Type",
            ["Expense", "Income"],
        )

        add_submitted = st.form_submit_button(
            "Add Category",
            use_container_width=True,
        )

        if add_submitted:
            if not new_category_name.strip():
                st.error("Please enter a category name.")
            else:
                try:
                    add_category(
                        new_category_name.strip(),
                        new_category_type,
                    )
                    st.success("Category added successfully!")
                    st.rerun()
                except Exception:
                    st.error("This category may already exist.")

    st.divider()
    st.markdown("#### Existing Categories")

    category_type_filter = st.radio(
        "Show Categories",
        ["Expense", "Income"],
        horizontal=True,
    )

    categories = get_categories(category_type_filter)

    for category in categories:
        category_id, category_name, category_type, colour = category

        col1, col2, col3 = st.columns([4, 1, 1])

        with col1:
            updated_name = st.text_input(
                "Category",
                value=category_name,
                key=f"category_{category_id}",
                label_visibility="collapsed",
            )

        with col2:
            if st.button(
                "Save",
                key=f"save_{category_id}",
                use_container_width=True,
            ):
                if updated_name.strip():
                    try:
                        rename_category(
                            category_id,
                            updated_name.strip(),
                        )
                        st.rerun()
                    except Exception:
                        st.error("Category name already exists.")
                else:
                    st.error("Category name cannot be empty.")

        with col3:
            if st.button(
                "Delete",
                key=f"delete_{category_id}",
                use_container_width=True,
            ):
                deleted = delete_category(category_id)

                if deleted:
                    st.rerun()
                else:
                    st.error(
                        "This category is used by a transaction "
                        "and cannot be deleted."
                    )

st.divider()
st.subheader("Expenses by Category")

chart_transactions = get_transactions()
chart_data = []

for transaction in chart_transactions:
    transaction_id, description, amount_pence, t_type, t_date, category_name = transaction

    if t_type == "Expense":
        chart_data.append({
            "Category": category_name,
            "Amount": amount_pence / 100
        })

if chart_data:
    df = pd.DataFrame(chart_data)
    category_totals = df.groupby("Category")["Amount"].sum()
    
    st.bar_chart(category_totals, horizontal=True)

else:
    st.info("Add some expenses to see your spending chart.")

st.divider()
st.subheader("Monthly Income vs Expenses")

monthly_transactions = get_transactions()
monthly_data = []

for transaction in monthly_transactions:
    transaction_id, description, amount_pence, t_type, t_date, category_name = transaction

    monthly_data.append({
        "Month": date.fromisoformat(t_date).strftime("%Y-%m"),
        "Type": t_type,
        "Amount": amount_pence / 100
    })

if monthly_data:
    monthly_df = pd.DataFrame(monthly_data)

    monthly_summary = monthly_df.pivot_table(
        index="Month",
        columns="Type",
        values="Amount",
        aggfunc="sum",
        fill_value=0
    )

    monthly_summary = monthly_summary.reindex(
        columns=["Income", "Expense"],
        fill_value=0
    )

    
    st.bar_chart(monthly_summary, stack=False)

else:
    st.info("Add transactions to see your monthly comparison.")
