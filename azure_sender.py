import json
import os
import time

from azure.eventhub import EventHubProducerClient, EventData

from stream_analytics.common.config import load_typed_config
from stream_analytics.generator.config_models import GeneratorConfig
from stream_analytics.generator.entities import generate_two_feeds_sample

# Load generator config from YAML (env vars with GENERATOR_ prefix override)
_cfg: GeneratorConfig = load_typed_config(
    relative_yaml_path="config/generator.yaml",
    model_type=GeneratorConfig,
    env_prefix="GENERATOR",
)

# Generate one batch for the order_events feed only
_order_events, _ = generate_two_feeds_sample(
    zone_count=_cfg.zone_count,
    restaurant_count=_cfg.restaurant_count,
    courier_count=_cfg.courier_count,
    sample_batch_size_per_feed=_cfg.sample_batch_size_per_feed or 500,
)

records = list(_order_events)


# ---------------------------------------------------------------------------
# Azure Event Hubs credentials
#
# Option A – environment variables (recommended, keeps secrets out of code):
#
#   Set these in your shell before running the script:
#
#   Windows PowerShell:
#     $env:EVENT_HUB_CONN_STR = "Endpoint=sb://<namespace>.servicebus.windows.net/;SharedAccessKeyName=<policy>;SharedAccessKey=<key>"
#     $env:EVENT_HUB_NAME     = "<your-event-hub-name>"
#
#   Bash / macOS / Linux:
#     export EVENT_HUB_CONN_STR="Endpoint=sb://<namespace>.servicebus.windows.net/;SharedAccessKeyName=<policy>;SharedAccessKey=<key>"
#     export EVENT_HUB_NAME="<your-event-hub-name>"
#
#   Where to find these values in the Azure Portal:
#     • Namespace connection string:
#         Azure Portal → Event Hubs namespace → "Shared access policies"
#         → select a policy (e.g. RootManageSharedAccessKey) → copy
#         "Connection string–primary key"
#     • Event Hub name:
#         Azure Portal → Event Hubs namespace → "Event Hubs" (left menu)
#         → the name listed there (e.g. "order-events")
#
# Option B – hard-code directly (quick local test only, never commit secrets):
#
#   Replace the os.environ lines below with:
#     connection_str = "Endpoint=sb://<namespace>.servicebus.windows.net/;SharedAccessKeyName=<policy>;SharedAccessKey=<key>"
#     eventhub_name  = "<your-event-hub-name>"
# ---------------------------------------------------------------------------

connection_str = os.environ["EVENT_HUB_CONN_STR"]

eventhub_name = os.environ["EVENT_HUB_NAME"]

client = EventHubProducerClient.from_connection_string(connection_str, eventhub_name=eventhub_name)


message_count = 0

# Group records by zone_id so each batch carries a partition_key.
# Event Hubs hashes the key to a partition, ensuring all events from
# the same zone land on the same partition while spreading zones across
# the available partitions.
from collections import defaultdict
zones: dict = defaultdict(list)
for record in records:
    zones[record["zone_id"]].append(record)

t0 = time.time()

with client:
    for zone_id, zone_records in zones.items():

        event_data_batch = client.create_batch(partition_key=zone_id)

        for record in zone_records:

            try:

                event_data_batch.add(EventData(json.dumps(record)))

                message_count += 1

            except ValueError:

                print("Batch full for zone " + zone_id + " – sending and continuing")

                client.send_batch(event_data_batch)

                event_data_batch = client.create_batch(partition_key=zone_id)

                event_data_batch.add(EventData(json.dumps(record)))

                message_count += 1

        client.send_batch(event_data_batch)

t1 = time.time()

tdiff = t1 - t0

print(str(message_count) + " messages sent to Event Hub " + str(eventhub_name) + " in " + str(int(tdiff)) + " seconds")
