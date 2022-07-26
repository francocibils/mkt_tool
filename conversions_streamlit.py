import pandas as pd
import streamlit as st
from conversions_functions import *
import json

# Import data
path = 'https://raw.githubusercontent.com/francocibils/mkt_tool/main/Conversions%20dataset.csv'
dataset = pd.read_csv(path, index_col = 0)

params_dict = json.load(open(r'C:\Users\HP\Desktop\SH - Profesional\Data Science and Machine Learning\Proyectos\My projects\Conversions tool\params_dict.json'))
products = [f'Product{i}' for i in range(1, 7)]
platforms = [f'Platform{i}' for i in range(1, 4)]

### Streamlit app

app_mode = st.sidebar.selectbox('Select Page', ['Home', 'Goal conversions cost', 'Cost of X amount of extra conversions', 'Profitable level of conversions', 'Investment range tool'])

if app_mode == 'Home':
    st.title('Conversions and costs')
    st.markdown('This is a simple toolbox that allows an online marketing manager improve the business decision-making process regarding conversions and investment in different media channels. Its main feature is that there is a diminishing returns relationship between investment and conversions, that is, the higher the amount of conversions the higher the cost to obtain one extra conversion. Another way of looking at it is that every extra dollar is going to yield less and less conversions the higher the amount of conversions we are already obtaining.')
    st.markdown('There are some assumptions behind this app:')
    st.markdown('1. There is no relationship between products and across platforms.')
    st.markdown('2. There is no adstock, which means that whatever money one invests in certain product and platform will only have an effect on the day it was invested.')
    st.markdown('3. There are no holidays, special events or promotions considered.')
    
    st.subheader('Dataset')
    st.markdown('I will be considering a synthetic dataset with 6 products across 3 different platforms. (Note: not all possible combinations between products and platforms are available.)')
    
    st.subheader('Tools')
    st.markdown('There are 4 tools available that aim to answer different business questions.')
    st.markdown('1. **Goal conversions cost**: Given that one aims to obtain X amount of conversions, how much are those X conversions going to cost?')
    st.markdown('2. **Cost of X amount of extra converions**: Given that one is already obtaining Y amount of conversions, how much are X extra conversions going to cost?')
    st.markdown('3. **Profitable level of conversions**: Given that conversions get more expensive the more we get, until what point is it profitable to get one extra conversion?')
    st.markdown('4. **Investment range to obtain X conversions**: Given that one aims to obtain X amount of conversions, what is the investment range that guarantees me, almost for sure, to obtain them?')

elif app_mode == 'Goal conversions cost':
    st.header('Get the cost of goal conversions')
    st.markdown('Define a daily or monthly goal of conversions for a product and a platform and get the expected cost of achieving that objective.')
    
    product = st.selectbox('Select a product', products)
    platform = st.selectbox('Select a platform', platforms)
    conversions_goal = st.number_input('Define conversions goal', min_value = 0)
    monthly_goal = st.checkbox('Monthly goal')

    if st.button('Get the cost'):
        try:
            result = get_conversions_cost(product, platform, params_dict, conversions_goal, monthly_goal)['Monthly cost']
            if monthly_goal:
                st.markdown(f'Obtaining **{conversions_goal}** monthly conversions is going to have a monthly cost of **{round(result, 2)}** dollars.')
            else:
                st.markdown(f'Obtaining **{conversions_goal}** daily conversions is going to have a monthly cost of **{round(result, 2)}** dollars.')
        except:
            st.error(f'**{product}** in **{platform}** does not exist.')

elif app_mode == 'Cost of X amount of extra conversions':
    st.header('Cost of X amount of extra conversions')
    st.markdown('Define a monthly or daily baseline level of conversions that you are already obtaining (or aim to obtain) and some amount of extra conversions above that level that you are interested in obtaining for a product and platform to get the CPC of those extra conversions.')
    
    product = st.selectbox('Select a product', products)
    platform = st.selectbox('Select a platform', platforms)
    base_conversions = st.number_input('Baseline conversions', min_value = 0)
    extra_conversions = st.number_input('Extra conversions from baseline', min_value = 0)
    monthly_goal = st.checkbox('Monthly goal')

    if st.button(f'Get the CPC of {extra_conversions} extra conversions from a baseline of {base_conversions} conversions.'):
        try:
            result = get_actual_cpc(product, platform, params_dict, base_conversions, extra_conversions, monthly_goal)['Actual CPC']
            if monthly_goal:
                st.markdown(f'Given a baseline of {base_conversions} monthly conversions, the CPC of getting {extra_conversions} extra monthly conversions is around {round(result, 2)}.')
            else:
                st.markdown(f'Given a baseline of {base_conversions} daily conversions, the CPC of getting {extra_conversions} extra daily conversions is around {round(result, 2)}.')
        except:
            st.error(f'**{product}** in **{platform}** does not exist.')

elif app_mode == 'Profitable level of conversions':
    st.header('Profitable level of conversions')
    st.markdown('For a product in a platform, define a baseline level of monthly or daily conversions, the amount of increases and the size of those increases and the conversion value to see at what point it is profitable to invest in that product and platform.')

    product = st.selectbox('Select a product', products)
    platform = st.selectbox('Select a platform', platforms)
    base_conversions = st.number_input('Baseline conversions', min_value = 0)
    monthly_goal = st.checkbox('Monthly goal')
    steps = st.number_input('How many increases?', min_value = 1)
    jumps = st.number_input('Jump size in each step?', min_value = 1)
    prof_threshold = st.number_input('Conversion value', min_value = 0)

    try:
        cpc_df = get_actual_cpc_line(product, platform, params_dict, base_conversions, steps, jumps, monthly_goal)
    except:
        st.error(f'**{product}** in **{platform}** does not exist.')

    if st.button('Get profitable level of conversions'):
        temp_df, result, warning = cpc_vs_threshold(cpc_df, prof_threshold)

        result_base_conversions = result['Base conversions']
        result_new_conversions = result['New conversions']
        result_actual_cpc = result['Actual CPC']

        if warning:
            st.text(warning)
            st.markdown('No profitable level found. Please set new parameters. Consider lowering baseline conversions if conversion value is lower than minimum CPC or increasing the amount of increases or the jump size if conversion value is higher than maximum CPC.')
            st.line_chart(temp_df.set_index('Daily base conversions')[['Actual CPC', 'Threshold']])
        else:
            st.markdown(f'The profitable level of conversions, given a conversion value of {prof_threshold} dollars, is around {round(result_base_conversions)} and {round(result_new_conversions)} conversions.')
            st.line_chart(temp_df.set_index('Daily base conversions')[['Actual CPC', 'Threshold']])

elif app_mode == 'Investment range tool':
    st.header('Recommended investment range to obtain X amount of conversions')
    st.markdown('One may be interested in knowing within what range of investment one may get a desired goal of conversions. For a product and platform, define a monthly or daily conversions goal and get the recommended monthly investment range to achieve that objective.')

    product = st.selectbox('Select a product', products)
    platform = st.selectbox('Select a platform', platforms)
    conversions_goal = st.number_input('Define conversions goal', min_value = 0)
    monthly_goal = st.checkbox('Monthly goal')

    if st.button(f'Get recommended investment range to obtain {conversions_goal} conversions'):
        try:
            result = get_investment_range(dataset, product, platform, conversions_goal, monthly_goal)
            optimistic_result = result['Optimistic']['Monthly cost']
            pessimistic_result = result['Pessimistic']['Monthly cost']
            st.markdown(f'For **{product}** in **{platform}** the model suggests that to obtain around **{conversions_goal}** conversions one should invest, on a monthly basis, between **{round(optimistic_result, 2)}** dollars and **{round(pessimistic_result, 2)}** dollars.')
        except:
            st.error(f'**{product}** in **{platform}** does not exist.')
