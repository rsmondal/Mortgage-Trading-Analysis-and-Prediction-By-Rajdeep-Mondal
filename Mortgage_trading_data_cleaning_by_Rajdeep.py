#!/usr/bin/env python
# coding: utf-8

# ## 1 Load the Data
# ### Import the datasets from the provided Excel files, 
# ### Use the pandas library in Python to load the data.

# In[1]:


import pandas as pd
import numpy as np


# In[2]:


loan_balances = pd.read_excel('loan_balances.xlsx')
loan_bids = pd.read_excel('loan_bids.xlsx')
loan_data = pd.read_excel('loan_data.xlsx')
loan_status = pd.read_excel('loan_status.xlsx')
target_profit = pd.read_excel('target_profit.xlsx')
umbs_prices = pd.read_excel('umbs_prices.xlsx')


# ## 2 Inspect the Data
# ### Display the first few rows of each dataset to understand the structure.
# ### Check for missing values in each dataset.
# 

# In[3]:


loan_balances.head(), loan_balances.info(), loan_balances.describe(), loan_balances.isnull().sum(),


# In[4]:


loan_bids.head(), loan_bids.info(), loan_bids.describe(), loan_bids.isnull().sum(),


# In[5]:


loan_data.head(), loan_data.info(), loan_data.describe(), loan_data.isnull().sum(),


# In[6]:


loan_status.head(), loan_status.info(), loan_status.describe(), loan_status.isnull().sum(),


# In[7]:


target_profit.head(), target_profit.info(), target_profit.describe(), target_profit.isnull().sum(),


# In[8]:


umbs_prices.head(), umbs_prices.info(), umbs_prices.describe(), umbs_prices.isnull().sum(),


# #### loan_balances, loan_bids, umbs_prices have no missing values.

# ## Handle missing values the missing values in loan_data.

# In[9]:


# Step 1: Handle missing values

# Fill 'total_loan_costs' with the median value
loan_data['total_loan_costs'].fillna(loan_data['total_loan_costs'].median(), inplace=True)

# Fill 'recurring_monthly_debt' with the median value
loan_data['recurring_monthly_debt'].fillna(loan_data['recurring_monthly_debt'].median(), inplace=True)

# Fill 'aus_type' with the mode value (most common value)
loan_data['aus_type'].fillna(loan_data['aus_type'].mode()[0], inplace=True)

# Drop columns with a large number of missing values
loan_data.drop(columns=['lender_credits', 'prepayment_pelty_term', 'intro_rate_period'], inplace=True)

# Step 2: Fix data types
# Convert columns with numeric data to numeric types
numeric_columns = ['total_loan_costs', 'recurring_monthly_debt', 'income_thousands', 'median_fico_score', 'target_profit']
loan_data[numeric_columns] = loan_data[numeric_columns].apply(pd.to_numeric, errors='coerce')

# Convert categorical columns to string type
categorical_columns = ['loan_type', 'loan_purpose', 'state_code', 'county', 'derived_loan_product_type', 'derived_dwelling_category', 'occupancy_type', 'manufactured_home', 'credit_score_type', 'aus_type', 'umbs_code']
loan_data[categorical_columns] = loan_data[categorical_columns].astype(str)

# Step 3: Drop duplicates
loan_data.drop_duplicates(inplace=True)

# Step 4: Standardize column names
loan_data.columns = loan_data.columns.str.lower().str.replace(' ', '_')

# Display the cleaned dataframe
loan_data.head()


# ### Handle missing values the missing values in target_profit.

# In[11]:


# Drop columns with a high proportion of missing values

target_profit.drop(columns=['lender_credits', 'prepayment_pelty_term', 'intro_rate_period', 
                   'acctual loan revenue', 'actual profit margin'], inplace=True)

# Drop rows with missing values in 'total_loan_costs', 'Gross Profit', and 'Profit Margin'
target_profit.dropna(subset=['total_loan_costs', 'Gross Profit', 'Profit Margin'], inplace=True)

# Fill missing values in 'recurring_monthly_debt' and 'aus_type' with the median
target_profit['recurring_monthly_debt'].fillna(target_profit['recurring_monthly_debt'].median(), inplace=True)
target_profit['aus_type'].fillna(target_profit['aus_type'].mode()[0], inplace=True)


# Remove duplicate rows
target_profit.drop_duplicates(inplace=True)

# Display the cleaned dataframe
target_profit.head()


# ### Handle missing values the missing values in  loan_status.

# In[16]:


# Step 1: Ensure date columns are in the correct format
date_columns = ['closing_date', 'file_in_audit', 'file_audit_complete', 'file_sent_to_custodian', 'file_at_custodian']
for column in date_columns:
    loan_status[column] = pd.to_datetime(loan_status[column], errors='coerce')

# Step 2: Remove duplicates
loan_status.drop_duplicates(inplace=True)

# Let's fill missing values for now with a placeholder date for better data handling later
# Placeholder date chosen as '1900-01-01' which is unlikely to conflict with actual dates
placeholder_date = '1900-01-01'

loan_status.fillna(placeholder_date, inplace=True)

# Ensure date columns are in the correct datetime format again after filling missing values
for col in date_columns:
    loan_status[col] = pd.to_datetime(loan_status[col], errors='coerce')

# Verify the changes
loan_status.head()


# # 4 Create Loan Statuses:
#    ### Define loan statuses based on the `current_balance` and `next_payment_due_date` in the `loan_balances` dataset.
# ### Create a new column `loan_status` to categorize the loans as 'Active', 'Closed', or 'Delinquent'.
# 

# In[18]:


# Convert date columns to datetime format
loan_balances['next_payment_due_date'] = pd.to_datetime(loan_balances['next_payment_due_date'])

# Define loan status based on current_balance and next_payment_due_date
def determine_loan_status(row):
    if row['current_balance'] == 0:
        return 'Closed'
    elif row['next_payment_due_date'] < pd.Timestamp.now() and row['current_balance'] > 0:
        return 'Delinquent'
    else:
        return 'Active'

loan_balances['loan_status'] = loan_balances.apply(determine_loan_status, axis=1)

# Save the updated dataset
loan_balances.to_csv('Documents/updated_loan_balances.csv', index=False)

loan_balances.head()


# # 5. Amortize Loan Balances:
#    ### Create a function to calculate the amortized balance for each loan in the `loan_balances` dataset.
#    ### Add a new column `amortized_balance` to the dataset with the calculated values.

# In[21]:


# Convert date columns to datetime format
loan_balances['next_payment_due_date'] = pd.to_datetime(loan_balances['next_payment_due_date'])

# Function to calculate the amortized balance
def calculate_amortized_balance(loan_amount, interest_rate, loan_term, payment_periods_made):
    # Monthly interest rate
    r = interest_rate / 12 / 100
    # Total number of payments
    N = loan_term * 12
    # Number of remaining payments
    n = N - payment_periods_made
    # Monthly payment (P)
    if r > 0:
        P = loan_amount * r * (1 + r)**N / ((1 + r)**N - 1)
        # Remaining balance (A)
        A = P * ((1 - (1 + r)**-n) / r)
    else:
        P = loan_amount / N
        A = loan_amount - (P * payment_periods_made)
    return A

# Apply the function to each row
loan_balances['amortized_balance'] = loan_balances.apply(
    lambda row: calculate_amortized_balance(
        row['loan_amount'], 
        row['interest_rate'], 
        row['loan_term'], 
        row['payment_periods_made']
    ), axis=1
)

# Save the updated dataset
loan_balances.to_csv('Documents/updated_loan_balances_with_amortized_balance.csv', index=False)

loan_balances.head()


# # 6. Merge Datasets:
#    ### Merge the loan_status, loan_data, target_profit, `loan_balances`, `umbs_prices`, and `loan_bids` datasets on relevant keys.
#    ### Ensure that the merged dataset is correctly joined and no important data is lost.

# In[32]:


umbs_prices.drop_duplicates(inplace=True)


# In[36]:


# Ensure the column names match for merging
loan_balances = loan_balances.rename(columns={'loan_id': 'loan_id'})
loan_bids = loan_bids.rename(columns={'loan_id': 'loan_id'})
loan_data = loan_data.rename(columns={'loan_id': 'loan_id'})
loan_status = loan_status.rename(columns={'loan_id': 'loan_id'})
target_profit = target_profit.rename(columns={'loan_id': 'loan_id'})
umbs_prices = umbs_prices.rename(columns={'umbs_code': 'umbs_code'})

# Merge datasets on loan_id
merged_df = loan_balances.merge(loan_data, on='loan_id', how='left')\
                         .merge(loan_status, on='loan_id', how='left')\
                         .merge(target_profit, on='loan_id', how='left')\
                         .merge(loan_bids, on='loan_id', how='left')


# Save the merged dataset
merged_df.to_csv('Documents/final_merged_dataset.csv', index=False)

# Display the first few rows of the merged dataset
merged_df.head()


# In[ ]:




