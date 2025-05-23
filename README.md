# ALEX: Argumentation System for Legal Explanations

This is the repository for ALEX, an Argumentation System for Legal Explanations. 


![alex-system](https://github.com/onspark/images/blob/main/demo_alex_low_res.gif)



# UPDATE
## Prompts Location

All project prompts can be found in the following directory:

`backend/app/prompts`


## Setup Instructions

1. Set up an `OPEN_AI_API` key in `backend/app/.env`. Replace 'YOUR API KEY' with your actual key.

   **WARNING!** 
   We use `GPT-4-turbo-preview` as our default model, which requires payment. Please refer to OpenAI's official website for details about the model.

2. Run `pip install -r requirements.txt` to install the required packages.

3. Run `setup_chroma_db.py` to build a chroma database for the repository. By default, it will include 126 Korean-to-English-translated fraud cases. You can add or change them in the `test\db_data` directory.

4. The default NLI (Natural Language Inference) model is `sentence-transformers/nli-bert-base`. Please note that the NLI model described in our paper is specifically trained on a mixture of general and legal Korean texts. This might lead to discrepancies in performance.

## Running the ALEX server (Backend)
The server component of ALEX is responsible for processing data and executing the core operation of the argumentation system. Follow these steps to start the server:

1. **Open a Terminal**: Access your command line or terminal application.

2. **Navigate to the Backend Directory**: Use the `cd` command to change your current directory to the `backend` folder of the ALEX repository.
   ```bash
   cd backend
   ```
3. **Start the server**: Execute the `run_alex.sh` script to start the server.

    ```bash
    bash run_alex.sh
    ```

## Running the ALEX User Interface (Frontend)
The visualization interface is built with Streamlit. It is designed to provide the user an intuitive overview of the generated network. Follow these steps to run the app:

1. **Open a new Terminal Window**: Separate from the one running the server.

2. **Navigate to the Frontend Directory**: Change to the `frontend` directory.

    ```bash
    cd frontend
    ```

3. **Run Streamlit**: Use Streamlit to start the frontend app.

    ```bash
    streamlit run app.py
    ```

## Loading a Generated Argumentation Network
To load a previously generated argumentation network, run the Streamlit app, then load the JSON file and click 'visualize'. 

![load-network](https://github.com/onspark/images/blob/main/load_json_demo.png)

This process can be used to load and review the case study test files in this repository.


## How to cite

This work was published in Artificial Intelligence and Law, 2025. 

```
@article{parkObjectionYourHonor2025,
  title = {Objection, Your Honor!: An {{LLM-driven}} Approach for Generating {{Korean}} Criminal Case Counterarguments},
  author = {Park, Sungmi and Choi, Ari and Park, Roseop},
  year = {2025},
  month = feb,
  journal = {Artificial Intelligence and Law},
  issn = {1572-8382},
  doi = {10.1007/s10506-025-09432-2}
}
```
