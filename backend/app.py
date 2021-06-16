import os
from pprint import pprint
import pretty_errors
from jina import Flow, Document, DocumentArray
from jina.parsers.helloworld import set_hw_chatbot_parser
import csv
from backend_config import backend_port, backend_workdir, backend_datafile
from executors import MyTransformer, MyIndexer


def trim_string(input_string: str, word_count: int = 50, sep: str = " ") -> str:
    """
    Trim a string to a certain number of words.
    :param input_string: string to trim
    :param word_count: how many words to trim to
    :param sep: separator between words
    :return: trimmmed string
    """
    sanitized_string = input_string.replace("\\n", sep)
    words = sanitized_string.split(sep)[:word_count]
    trimmed_string = " ".join(words)

    return trimmed_string


def prep_docs(input_file: str) -> DocumentArray:
    """
    Create DocumentArray consisting of every row in csv as a Document
    :param input_file: Input csv filename
    :return: populated DocumentArray
    """
    docs = DocumentArray()
    with open(input_file, "r") as csv_file:
        csv_reader = csv.DictReader(csv_file)
        input_field = "Description"
        for row in csv_reader:
            input_data = trim_string(row[input_field])
            doc = Document(text=input_data)
            doc.tags = row
            docs.extend([doc])

    return docs


def run_appstore_flow(inputs, args) -> None:
    """
    Execute the app store example. Indexes data and presents REST endpoint
    :param inputs: Documents or DocumentArrays to input
    :args: arguments like port, workdir, etc
    :return: None
    """

    # Create Flow and add
    #   - MyTransformer (an encoder Executor)
    #   - MyIndexer (a simple indexer Executor)
    flow = (
        Flow()
        .add(uses=MyTransformer, parallel=args.parallel)
        .add(uses=MyIndexer, workspace=args.workdir)
    )

    # Open the Flow
    with flow:
        # Start index pipeline, taking inputs then printing the processed DocumentArray
        flow.post(on="/index", inputs=inputs, on_done=print)
        
        # Start REST gateway so clients can query via Streamlit or other frontend (like Jina Box) 
        flow.use_rest_gateway(args.port_expose)

        # Block the process to keep it open. Otherwise it will just close and no-one could connect
        flow.block()


if __name__ == "__main__":

    # Get chatbot's default arguments
    args = set_hw_chatbot_parser().parse_args()

    # Change a few things
    args.port_expose = backend_port
    args.workdir = backend_workdir

    # Convert the csv file to a DocumentArray
    docs = prep_docs(input_file=backend_datafile)

    # Run the Flow
    run_appstore_flow(inputs=docs, args=args)
