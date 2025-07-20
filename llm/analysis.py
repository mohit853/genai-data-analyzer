import os, re, json, base64
from datetime import datetime
from llm.openai import call_llm_api
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import shutil


##! prints missing values in console
def analyze_missing_values(df):  
    """Analyze and report missing values in the dataset."""
    missing_values = df.isnull().sum()
    print("Missing Values:\n", missing_values)
    return missing_values

##! prints outliers in console
def detect_outliers(df):
    """Detect outliers in numerical columns using the IQR method."""
    outlier_summary = {}
    num_cols = df.select_dtypes(include="number").columns.tolist()
    for col in num_cols:
        Q1 = df[col].quantile(0.25)
        Q3 = df[col].quantile(0.75)
        IQR = Q3 - Q1
        outliers = df[(df[col] < (Q1 - 1.5 * IQR)) | (df[col] > (Q3 + 1.5 * IQR))]
        outlier_summary[col] = len(outliers)
    print("Outlier Summary:", outlier_summary)
    return outlier_summary


##! stores correlation matrix as an image file in ouytput directory
def correlation_analysis(df):
    """Compute and visualize correlation matrix for numerical features."""
    num_cols = df.select_dtypes(include="number").columns  # Create the output directory if it doesn't exis
    os.makedirs("output", exist_ok=True)
    if len(num_cols) > 1:
        corr = df[num_cols].corr()
        plt.figure(figsize=(8, 6))
        sns.heatmap(corr, annot=True, cmap="coolwarm", fmt=".2f")
        plt.title("Correlation Matrix")
        corr_file = "output/correlation_matrix.png"
        plt.savefig(corr_file)
        plt.close()
        print("Correlation analysis complete.")
        return corr_file
    return None

##! Generate histogram and boxplots in output directory
def generate_visualizations(df):
    """Generate visualizations based on dataset statistics."""
    images = []
    plt.style.use("seaborn-v0_8-darkgrid")
    os.makedirs("output", exist_ok=True)
    # Histogram for numerical columns
    num_cols = df.select_dtypes(include="number").columns
    ## ^ Histogram for the first 3 numerical columns
    for col in num_cols[:3]:
        plt.figure(figsize=(8, 6))
        df[col].plot(kind="hist", bins=20, color="skyblue", edgecolor="black")
        plt.title(f"Distribution of {col}")
        plt.xlabel(col)
        plt.ylabel("Frequency")
        hist_file = os.path.join("output", f"{col}_histogram.png")
        plt.savefig(hist_file, dpi=100)
        images.append(hist_file)
        plt.close()

    # Boxplot of all numerical columns
    if len(num_cols) > 0:
        plt.figure(figsize=(10, 6))
        df[num_cols].boxplot()
        plt.title("Box Plot of Numerical Columns")
        boxplot_file = os.path.join("output", f"{col}boxplot.png")
        plt.savefig(boxplot_file, dpi=100)
        images.append(boxplot_file)
        plt.close()

    return images



##! LLM generates summary for given missing values and outlier summary 
def get_self_analysis_summary(missing_values, outlier_summary):
    text = f"""
    You are an expert data scientist. Give me summary of this analysis.

    Given below is the analysys:
    Missing Values: {missing_values}
    Outlier Summary: {outlier_summary}
    
    """
    prompt_content = create_prompt_content(text, images_path=[])
    response = call_llm_api(prompt_content)
    print("Self Analysis Summary:", response)
    return response


def encode_image(image_path):
    """Encodes image to base64."""
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")



##! Create prompt content with text and images for multimodal LLM API
def create_prompt_content(
    text, images_path
):  ## it converts the text and images into a format suitable for the LLM API
    """Creates the prompt content with multiple base64 encoded images."""
    content = [{"type": "text", "text": text}]  # Starting with the text part
    if len(images_path) > 0:
        for image_path in images_path:
            base64_image = encode_image(image_path)  # Encode the current image
            image_content = {
                "type": "image_url",
                "image_url": {
                    "url": f"data:image/jpeg;base64,{base64_image}",
                    "detail": "low",  # Low resolution for all images, adjust if necessary
                },
            }
            content.append(image_content)  # Add each image to the content

    return content


def convert_data_types(data_types):
    """Helper function to convert pandas data types to Python native types for JSON serialization."""
    return {key: str(value) for key, value in data_types.items()}

##! llm generates python code and visulazions based on the dataframe 
def interactive_analysis_using_llm(df, filename):
    # Prepare the dataset summary
    summary = {
        "filename": filename,
        "columns": list(df.columns),
        "data_types": convert_data_types(
            df.dtypes.to_dict()
        ),  # Convert pandas types to native types
        "num_rows": len(df),
        "num_columns": len(df.columns),
        "summary_statistics": df.describe().to_dict(),
        "example_values": df.head().to_dict(),  # Show first 5 rows as example
    }

    prompt = f"""
You are an expert data scientist. I have a dataset with the following summary:

Filename: {summary['filename']}
Columns: {summary['columns']}
Data Types: {json.dumps(summary['data_types'], indent=2)}
Number of Rows: {summary['num_rows']}
Number of Columns: {summary['num_columns']}
Summary Statistics: {json.dumps(summary['summary_statistics'], indent=2)}
Example Values: {json.dumps(summary['example_values'], indent=2)}

ONLY Provide Python code.
Based on above summary, separate numerical and categorical columns and suggest the Basic analysis I can perform (For example, summary statistics, counting missing values, correlation matrices, outliers). 
Don't add countplot for categorical columns

if you provide any plots then save them in current directory (use seaborn)
If you suggest a function call, please also explain why it's useful.

read file using:
with open(csv_file, 'rb') as f:
    encoding_result = chardet.detect(f.read())
df = pd.read_csv(csv_file, encoding=encoding_result['encoding'])
"""
    # prompt_content = create_prompt_content(
    #     prompt, images_path=[]
    # )  # ^ passing empty list for images
    response = call_llm_api(prompt)
    code_snippets = re.findall(r"```python(.*?)```", response, re.DOTALL)

    # Execute each code snippet and save its result
    results = {}
    for idx, code in enumerate(code_snippets):
        try:
            # Create a unique key for each snippet
            snippet_name = f"snippet_{idx + 1}"

            # Redirect the output of exec to capture the results
            # exec_globals = {}
            exec_globals = {"plt": plt, "sns": sns, "pd": pd, "df": df}
            exec(code, exec_globals)

            # If the code generates any output, capture and save it
            # Assuming the code generates variables of interest that you want to store
            results[snippet_name] = exec_globals

        except Exception as e:
            print(f"Error executing LLM-suggested code: {e}")
            results[f"snippet_{idx + 1}"] = str(e)

    return {"response": response, "results": results}



##! llm genrates summary of the data given dataframe information only
def get_data_summary(df, filename):
    summary = {
        "filename": filename,
        "columns": list(df.columns),
        "data_types": convert_data_types(
            df.dtypes.to_dict()
        ),  # Convert pandas types to native types
        "num_rows": len(df),
        "num_columns": len(df.columns),
        "summary_statistics": df.describe().to_dict(),
        "example_values": df.head().to_dict(),  # Show first 5 rows as example
    }

    text = f"""
    You are an expert data scientist. Give me summary of this data.
    
    Filename: {summary['filename']}
    Columns: {summary['columns']}
    Data Types: {json.dumps(summary['data_types'], indent=2)}
    Number of Rows: {summary['num_rows']}
    Number of Columns: {summary['num_columns']}
    Summary Statistics: {json.dumps(summary['summary_statistics'], indent=2)}
    Example Values: {json.dumps(summary['example_values'], indent=2)}
    
    """
    prompt_content = create_prompt_content(text, images_path=[])
    response = call_llm_api(prompt_content)
    return response


##! summarize llm generated text response 
def get_analysis_carried_out(response):
    prompt = f"""
    You are an expert data scientist. Give me summary of analysis you carried out.

    Given below is the analysys:
    {response}
    
    """
    prompt_content = create_prompt_content(prompt, images_path=[])
    response = call_llm_api(prompt_content)
    return response


##! gets insights from images specifically generated by LLM code  
def get_insights_discovered(results):
    images_path = [file for file in os.listdir(".") if file.endswith(".png")]
    prompt = f"""
    You are an expert data scientist. Give me the insights you discovered from the analysis.

    Given below are the analysys results:
    {results}
    
    """
    prompt_content = create_prompt_content(prompt, images_path)
    response = call_llm_api(prompt_content)
    return response


def create_story(
    self_analysis_summary, data_summary, analysis_carried_out, analysis_results
):
    images_path = [file for file in os.listdir(".") if file.endswith(".png")]
    text = f"""
You are a data analyst. Narrate a story about the analysis you performed in very Detail. Add these points in the story in detail
    1. The data you received, briefly
    2. The analysis you carried out
    3. The insights you discovered
    4. The implications of your findings (i.e. what to do with the insights)


Data Summary Before applying any change to data: {self_analysis_summary}






Data Summary After applying some changes to data : {data_summary}







Analysis Carried Out : {analysis_carried_out}






Analysis Results : {analysis_results}
"""

    prompt_content = create_prompt_content(text, images_path)
    story = call_llm_api(prompt_content)
    return story


def generate_readme(story, visualizations):
    """Generate README.md file combining the story and visualizations."""
    with open("README.md", "w") as f:
        f.write("# Automated Analysis Report\n\n")
        f.write(f"Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write("## Analysis Summary\n\n")
        f.write(story + "\n\n")
        f.write("## Visualizations\n\n")

        print("README.md file has been created.")


def move_pngs_to_llm_outputs():
    """Move all .png files in current dir to llm_outputs folder if not already there."""
    os.makedirs("llm_outputs", exist_ok=True)
    for file in os.listdir("."):
        if file.endswith(".png"):
            source = os.path.join(".", file)
            destination = os.path.join("llm_outputs", file)
            if not os.path.exists(destination):
                shutil.move(source, destination)
                print(f"Moved: {file} -> llm_outputs/{file}")
