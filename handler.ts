import { app, HttpRequest, HttpResponseInit } from "@azure/functions";

app.http("query", {
  methods: ["POST"],
  authLevel: "function",
  route: "query",
  handler: async (_request: HttpRequest): Promise<HttpResponseInit> => {
    return {
      status: 200,
      body: {},
    };
  },
});

export default app;
