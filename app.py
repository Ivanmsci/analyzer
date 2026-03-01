import os
import google.generativeai as genai
import pandas as pd
from flask import Flask, render_template, request, redirect, flash
import markdown

app = Flask(__name__)
app.secret_key = 'supersecretkey'  # Needed for flash messages

# Configure Google Generative AI
# Expects GOOGLE_API_KEY to be set in environment variables
GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY")
if GOOGLE_API_KEY:
    genai.configure(api_key=GOOGLE_API_KEY)

@app.route('/', methods=['GET'])
def index():
    return render_template('index.html')

@app.route('/analyze', methods=['POST'])
def analyze():
    if not GOOGLE_API_KEY:
        flash("Error: GOOGLE_API_KEY environment variable not set.", "error")
        return redirect('/')

    if 'file' not in request.files:
        flash("No file part", "error")
        return redirect('/')
    
    file = request.files['file']
    
    if file.filename == '':
        flash("No selected file", "error")
        return redirect('/')

    if file:
        try:
            # Determine file type and read into DataFrame
            if file.filename.endswith('.csv'):
                df = pd.read_csv(file)
            elif file.filename.endswith(('.xls', '.xlsx')):
                df = pd.read_excel(file)
            else:
                flash("Invalid file type. Please upload CSV or Excel.", "error")
                return redirect('/')

            # Convert DataFrame to CSV string for the AI
            data_as_string = df.to_csv(index=False)

            # Limit data size if necessary to avoid token limits (optional safety)
            # data_as_string = data_as_string[:100000] 

            prompt = f"""
            Act as a data analyst. Analyze the following dataset and provide:
            1. Key Trends and Insights (correlations, outliers, patterns).
            2. A brief Forecast/Prediction based on the historical data provided.

            Dataset:
            {data_as_string}
            """

            model = genai.GenerativeModel('gemini-2.5-flash')
            response = model.generate_content(prompt)
            
            # Convert Markdown to HTML for display
            analysis_html = markdown.markdown(response.text)

            return render_template('result.html', analysis=analysis_html)

        except Exception as e:
            flash(f"An error occurred during analysis: {str(e)}", "error")
            return redirect('/')

    return redirect('/')

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(debug=True, host='0.0.0.0', port=port)
