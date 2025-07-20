import matplotlib.pyplot as plt
import seaborn as sns
import json
import re
import requests
import time
from datetime import datetime
import base64
import chardet


from sklearn.decomposition import PCA
from llm.openai import call_llm_api
from llm.analysis import (
    analyze_missing_values,
    detect_outliers,
    correlation_analysis,
    generate_visualizations,
    get_self_analysis_summary,
    create_prompt_content,
    encode_image,
    convert_data_types,
    interactive_analysis_using_llm,
    get_data_summary,
    get_analysis_carried_out,
    get_insights_discovered,
    create_story,
    generate_readme,
    move_pngs_to_llm_outputs,
)
from file_upload import df, csv_file


def main():
    """Main function to execute the analysis."""

    # Analyze missing values of dataframe
    missing_values = analyze_missing_values(df)

    # Detect outliers
    outlier_summary = detect_outliers(df)

    # Perform correlation analysis
    corr_file = correlation_analysis(df)

    # Generate visualizations
    visualizations = []
    if corr_file:
        visualizations.append(corr_file)

    images = generate_visualizations(df)
    visualizations.extend(images)  ## ^ Copy images into new list visulizations

    # Perform Interactive Analysis
    a = interactive_analysis_using_llm(df, csv_file)
    response = a["response"]             ## returns python code from function   
    results = a["results"]               ## returns all varaibles and libraries used in the code by function

    time.sleep(3)
    move_pngs_to_llm_outputs()

    
    data_summary = get_data_summary(df, csv_file)
    time.sleep(3)

    analysis_carried_out = get_analysis_carried_out(response)
    time.sleep(3)

    analysis_results = get_insights_discovered(results)
    time.sleep(3)


    self_analysis_summary = get_self_analysis_summary(missing_values, outlier_summary)
    time.sleep(3)

    story = create_story(
        self_analysis_summary, data_summary, analysis_carried_out, analysis_results
    )
    move_pngs_to_llm_outputs()
    generate_readme(story, visualizations)
    move_pngs_to_llm_outputs()

if __name__ == "__main__":
    main()
