import pandas as pd
from flask import Flask, render_template, request, jsonify

# Load dataset
df = pd.read_csv("employment_dataset.csv")
df['Posted Date'] = pd.to_datetime(df['Posted Date'])
df['Country'] = df['Location'].apply(lambda x: x.split(',')[-1].strip())
df['Experience Level'] = df['Experience Level'].str.title()

app = Flask(__name__)

@app.route('/')
def index():
    """Render the main dashboard page"""
    industries = sorted(df['Industry'].dropna().unique().tolist())
    countries = sorted(df['Country'].dropna().unique().tolist())
    return render_template('index.html', 
                          industries=industries, 
                          countries=countries)

@app.route('/api/data', methods=['GET'])
def get_data():
    """API endpoint to get filtered data for D3 visualizations"""
    # Get filter parameters
    selected_industries = request.args.getlist('industry')
    selected_countries = request.args.getlist('country')
    
    # Filter data
    dff = df.copy()
    if selected_industries:
        dff = dff[dff['Industry'].isin(selected_industries)]
    if selected_countries:
        dff = dff[dff['Country'].isin(selected_countries)]
    
    # Prepare data for D3 visualizations
    # 1. Bar chart data: Average salary by experience level
    bar_data = dff.groupby('Experience Level')['Salary (USD)'].mean().reset_index()
    bar_data = bar_data.sort_values('Salary (USD)', ascending=False)
    bar_data = bar_data.to_dict(orient='records')
    
    # 2. Pie chart data: Employment Type
    pie_data = dff['Employment Type'].value_counts().reset_index()
    pie_data.columns = ['name', 'value']
    pie_data = pie_data.to_dict(orient='records')
    
    # 3. Line plot data: Job postings over time
    timeline = dff.groupby(dff['Posted Date'].dt.to_period("M")).size().reset_index(name='count')
    timeline['month'] = timeline['Posted Date'].dt.strftime('%Y-%m')
    timeline = timeline[['month', 'count']].to_dict(orient='records')
    
    # 4. Scatter plot data: Salary vs Experience
    scatter_data = dff[['Experience Level', 'Salary (USD)', 'Industry']].to_dict(orient='records')
    
    # 5. Tree map data: Jobs by Industry and Country
    tree_data = []
    for country in dff['Country'].unique():
        country_data = {
            "name": country,
            "children": []
        }
        country_df = dff[dff['Country'] == country]
        for industry in country_df['Industry'].unique():
            industry_df = country_df[country_df['Industry'] == industry]
            industry_data = {
                "name": industry,
                "value": int(industry_df['Salary (USD)'].sum())
            }
            country_data["children"].append(industry_data)
        tree_data.append(country_data)
    tree_data = {"name": "root", "children": tree_data}
    
    # 6. Parallel coordinates data
    parallel_data = dff[['Experience Level', 'Industry', 'Salary (USD)']].dropna().to_dict(orient='records')
    
    # Combine all data
    data = {
        'bar_data': bar_data,
        'pie_data': pie_data,
        'line_data': timeline,
        'scatter_data': scatter_data,
        'tree_data': tree_data,
        'parallel_data': parallel_data,
        'experience_levels': sorted(dff['Experience Level'].unique().tolist()),
        'industries': sorted(dff['Industry'].unique().tolist())
    }
    
    return jsonify(data)

if __name__ == '__main__':
    print("Starting Flask app...")
    app.run(debug=True, port=8050)