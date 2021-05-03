requests = {
    {path = "/data/10000000_3_125000000/0"},
    {path = "/data/10000000_3_125000000/1"},
    {path = "/data/10000000_3_125000000/2"},
    {path = "/data/10000000_3_125000000/3"},
    {path = "/data/10000000_3_125000000/4"},
    {path = "/data/10000000_3_125000000/5"},
    {path = "/data/10000000_3_125000000/6"},
    {path = "/data/10000000_3_125000000/7"},
    {path = "/data/10000000_3_125000000/8"},
    {path = "/data/10000000_3_125000000/9"},
    {path = "/data/10000000_3_125000000/10"},
    {path = "/data/10000000_3_125000000/11"},
    {path = "/data/10000000_3_125000000/12"},
    {path = "/data/10000000_3_125000000/13"},
    {path = "/data/10000000_3_125000000/14"},
    {path = "/data/10000000_3_125000000/15"},
    {path = "/data/10000000_3_125000000/16"},
    {path = "/data/10000000_3_125000000/17"},
    {path = "/data/10000000_3_125000000/18"},
    {path = "/data/10000000_3_125000000/19"},
    {path = "/data/10000000_3_125000000/20"},
    {path = "/data/10000000_3_125000000/21"},
    {path = "/data/10000000_3_125000000/22"},
    {path = "/data/10000000_3_125000000/23"},
    {path = "/data/10000000_3_125000000/24"},
    {path = "/data/10000000_3_125000000/25"},
    {path = "/data/10000000_3_125000000/26"},
    {path = "/data/10000000_3_125000000/27"},
    {path = "/data/10000000_3_125000000/28"},
    {path = "/data/10000000_3_125000000/29"},
    {path = "/data/10000000_3_125000000/30"},
    {path = "/data/10000000_3_125000000/31"},
    {path = "/data/10000000_3_125000000/32"},
    {path = "/data/10000000_3_125000000/33"},
    {path = "/data/10000000_3_125000000/34"},
    {path = "/data/10000000_3_125000000/35"},
    {path = "/data/10000000_3_125000000/36"},
    {path = "/data/10000000_3_125000000/37"},
}

print(requests[1])

if #requests <= 0 then
  print("multiplerequests: No requests found.")
  os.exit()
end

print("multiplerequests: Found " .. #requests .. " requests")

counter = 1
request = function()
  -- Get the next requests array element
  local request_object = requests[counter]

  -- Increment the counter
  counter = counter + 1

  -- If the counter is longer than the requests array length -> stop and exit
  if counter > #requests then
    wrk.thread:stop()
    os.exit()
  end

  -- Return the request object with the current URL path
  return wrk.format(request_object.method, request_object.path, request_object.headers, request_object.body)
end
        