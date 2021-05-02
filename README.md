# Will it Saturate?
> Just a test to see if we are abe to saturate 1Gbit with file responsens using just pure Python without nginx or something like that. 


```python
%load_ext nb_black
```


    <IPython.core.display.Javascript object>


This file will become your README and also the index of your documentation.

## Install

`pip install will_it_saturate`

## How to use

Start control server

`wis_control_server`

```python
import httpx
import pandas as pd

from urllib.parse import urljoin

from will_it_saturate import servers
from will_it_saturate import clients
from will_it_saturate.epochs import Epoch
from will_it_saturate.hosts import Host, HostDetails

from will_it_saturate.results import Result
from will_it_saturate.files import BenchmarkFile
from will_it_saturate.control.client import ControlClient
from will_it_saturate.repositories import SqliteRepository, register_default_tables
```


    <IPython.core.display.Javascript object>


### Create Benchmark Server

create server control client + server (needed for turning files into urls)

```python
# dont_test

server_control_host = Host(name="localhost", port=8001)
server_control_client = ControlClient(host=server_control_host)
server_details = server_control_client.get_host_details()
server = server_control_client.get_or_create_server(
    servers.FastAPIUvicornServer(host="localhost", port=5001)
)
```


    <IPython.core.display.Javascript object>


### Create Files and Urls

```python
# dont_test

byte, file_size, duration = 8, 10 ** 7, 3
epoch = Epoch(file_size=file_size, duration=duration)
files = server_control_client.get_or_create_files(epoch)
epoch.urls = [server.file_to_url(file) for file in files]
```


    <IPython.core.display.Javascript object>


### Create Control Client

```python
# dont_test

client_control_host = Host(name="localhost", port=8001)
client_control_client = ControlClient(host=client_control_host)
client_details = client_control_client.get_host_details()
benchmark_client = clients.HttpxClient(name="httpx")
```


    <IPython.core.display.Javascript object>


### Create Result

```python
# dont_test

result = Result(
    server=server,
    client=benchmark_client,
    server_details=server_details,
    client_details=client_details,
    file_size=epoch.file_size,
    complete_size=epoch.complete_size,
)
```


    <IPython.core.display.Javascript object>


### Measure Server with Client

```python
# dont_test

result.elapsed = client_control_client.measure(benchmark_client, epoch)
```


    <IPython.core.display.Javascript object>


### Save Result

We are using a sqlite database for saving benchmark results.

```python
# dont_test

repository = SqliteRepository.build_repository("results.db")
register_default_tables(repository)
results = repository.tables["result"]
```


    <IPython.core.display.Javascript object>


```python
# dont_test

result_id = results.add_result(result)
```


    <IPython.core.display.Javascript object>


```python
# dont_test

results_from_database = results.get_results()

cols = set(["server", "client", "elapsed", "file_size_h", "bytes_per_second_h"])
pd.DataFrame(
    [
        {k: v for k, v in r.dict_for_pandas().items() if k in cols}
        for r in results_from_database
    ]
)
```




<div>
<style scoped>
    .dataframe tbody tr th:only-of-type {
        vertical-align: middle;
    }

    .dataframe tbody tr th {
        vertical-align: top;
    }

    .dataframe thead th {
        text-align: right;
    }
</style>
<table border="1" class="dataframe">
  <thead>
    <tr style="text-align: right;">
      <th></th>
      <th>server</th>
      <th>client</th>
      <th>elapsed</th>
      <th>file_size_h</th>
      <th>bytes_per_second_h</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <th>0</th>
      <td>fastAPI/uvicorn</td>
      <td>httpx</td>
      <td>4.318646</td>
      <td>9.54MB</td>
      <td>82.81MB</td>
    </tr>
    <tr>
      <th>1</th>
      <td>fastAPI/uvicorn</td>
      <td>httpx</td>
      <td>3.168980</td>
      <td>9.54MB</td>
      <td>112.85MB</td>
    </tr>
  </tbody>
</table>
</div>




    <IPython.core.display.Javascript object>

