{
  "graphiteHost": "127.0.0.1",
  "graphitePort": 2003,
  "debug": true,
  "dumpMessages": true,
  "port": 8125,
  "flushInterval": 10000,
  "percentThreshold": [50, 90, 95, 99],
  "servers": [
      { server: "./servers/udp", address: "0.0.0.0", port: 8125 }
  ],
  "histogram": [
    {
        metric: 'request.time',
        bins: [ 5, 10, 50, 100, 200, 400, 'inf']
    }
  ]
}