import os
from datetime import UTC, datetime, timedelta

import dlt
from dotenv import load_dotenv
from logfire.query_client import LogfireQueryClient

load_dotenv()

@dlt.resource(name="records", write_disposition="replace")
def logfire_records():
    api_key = os.environ["LOGFIRE_API_KEY"]
    min_timestamp = datetime.now(tz=UTC) - timedelta(days=1)

    with LogfireQueryClient(read_token=api_key) as client:
        result = client.query_json_rows(
            """
            SELECT trace_id, span_id, start_timestamp, end_timestamp,
                   message, attributes
            FROM records
            """,
            min_timestamp=min_timestamp,
        )
        for row in result["rows"]:
            yield row


if __name__ == "__main__":
    pipeline = dlt.pipeline(
        pipeline_name="logfire_pipeline",
        destination="duckdb",
        dataset_name="agent_traces",
    )
    load_info = pipeline.run(logfire_records())
    print(load_info)
