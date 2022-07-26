import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import statsmodels.api as sm

from matplotlib.ticker import FormatStrFormatter
import matplotlib as mpl
import matplotlib.dates as mdates

def transform_column(column, dataframe):
        
    return np.sqrt(dataframe[column])

def fit_results(dataframe, y_column, x_columns, constant = True):
    
    y = dataframe[y_column]
    x = dataframe[x_columns]
    
    if constant:
        x = sm.add_constant(x)
        
    model = sm.OLS(y, x)
    results = model.fit()
    
    return results

def get_results(df, variable):
    
    temp = df[[variable + ' - Investment', variable + ' - Conversions']].copy(deep = True)
    temp = temp.loc[~(temp == 0).any(axis = 1)]
    temp[variable + ' - Investment_sqrt'] = transform_column([variable + ' - Investment'], temp)

    y = [variable + ' - Conversions']
    x = [variable + ' - Investment_sqrt']
    
    results = fit_results(temp, y, x, constant = True)

    return results

def get_conversions_cost(product, platform, params_dict, goal_conversions, monthly_goal = True):
    
    params = params_dict[f'{product} - {platform}']
    const = params[0]
    coeff = params[1]
    
    # If monthly_goal is set to True, divide goal_conversions by 30 to get daily goal, since the model is for daily data. Then, multiply cost by 30 to get monthly cost
    if monthly_goal:
        goal_conversions = goal_conversions / 30
        
    daily_cost = ((goal_conversions - const) / coeff) ** 2
    monthly_cost = daily_cost * 30
    cpc = daily_cost / goal_conversions
    
    return {'Monthly cost': monthly_cost, 'Daily cost': daily_cost, 'Cost per conversion': cpc}

def get_actual_cpc(product, platform, params_dict, base_conversions, extra_conversions, monthly_goal = True):
    
    params = params_dict[f'{product} - {platform}']
    const = params[0]
    coeff = params[1]
    
    new_conversions = base_conversions + extra_conversions
    
    if monthly_goal:
        base_conversions = base_conversions / 30
        new_conversions = new_conversions / 30
        
    # Get delta of conversions
    conversions_change = new_conversions - base_conversions
    
    # Get delta of cost
    cost_base = ((base_conversions - const) / coeff) ** 2
    cost_new = ((new_conversions - const) / coeff) ** 2
    cost_change = cost_new - cost_base
    
    # Get CPC
    cpc = cost_change / conversions_change
    
    return {'Daily base conversions': base_conversions, 'Daily new conversions': new_conversions, 'Actual CPC': cpc}

def get_actual_cpc_line(product, platform, params_dict, base_conversions, steps = 100, jump = 1, monthly_goal = True):
    
    params = params_dict[f'{product} - {platform}']
    const = params[0]
    coeff = params[1]
    
    if monthly_goal:
        base_conversions = base_conversions / 30
        
    new_conversions = base_conversions + jump
    
    cpc_dict = {}
    
    for i in range(steps):
        # Get delta of conversions
        conversions_change = new_conversions - base_conversions

        # Get delta of cost
        cost_base = ((base_conversions - const) / coeff) ** 2
        cost_new = ((new_conversions - const) / coeff) ** 2
        cost_change = cost_new - cost_base

        # Get CPC
        cpc = cost_change / conversions_change
        
        cpc_dict[i] = {'Daily base conversions': base_conversions, 'Daily new conversions': new_conversions, 'Actual CPC': cpc}
        
        base_conversions += jump
        new_conversions += jump

    df = pd.DataFrame.from_dict(cpc_dict).T
        
    return df

def cpc_vs_threshold(df, threshold_value):
    
    temp = df.copy(deep = True)
    temp['Threshold'] = threshold_value
    
    warning = ''

    if threshold_value < temp['Actual CPC'].min():
        warning = f"WARNING: Chosen threshold value {threshold_value} is lower than CPC minimum {round(temp['Actual CPC'].min(), 2)}."
    elif threshold_value > temp['Actual CPC'].max():
        warning = f"WARNING: Chosen threshold value {threshold_value} is higher than CPC maximum {round(temp['Actual CPC'].max(), 2)}."
       
    closest_index = temp['Actual CPC'].sub(threshold_value).abs().idxmin()
    closest_value = {
        'Base conversions': temp.iloc[closest_index]['Daily base conversions'],
        'New conversions': temp.iloc[closest_index]['Daily new conversions'],
        'Actual CPC': temp.iloc[closest_index]['Actual CPC']
    }
        
    return temp, closest_value, warning
        

def get_investment_range(dataset, product, platform, goal_conversions, monthly_goal = True):
    
    # Get confidence interval for both coefficients
    conf_int = get_results(dataset, f'{product} - {platform}').conf_int(alpha = 0.05)
    
    params = {}
    params['Optimistic'] = conf_int[1].to_list()
    params['Pessimistic'] = conf_int[0].to_list()
    
    # Get investment levels
    investment_range = {}
    
    if monthly_goal:
            goal_conversions = goal_conversions / 30
    
    for i in ['Optimistic', 'Pessimistic']:
        const = params[i][0]
        coeff = params[i][1]
        
        daily_cost = ((goal_conversions - const) / coeff) ** 2
        monthly_cost = daily_cost * 30
        
        investment_range[i] = {'Daily cost': daily_cost, 'Monthly cost': monthly_cost}
        
    return investment_range