# Live rollout checklist

1. Confirm `curl` from the Home Assistant host authenticates to
   `http://hermes.example-tailnet.ts.net:8642/v1/capabilities`.
2. Add Hermes Assistant in Home Assistant and confirm it loads without warnings.
3. Open the Hermes service device and confirm the conversation and diagnostic
   connectivity entities are grouped under it.
4. Confirm the connectivity entity reports connected, then stop the Hermes
   gateway and confirm it reports disconnected within about 60 seconds.
5. Restart Hermes and confirm connectivity returns without reloading the
   integration.
6. Use **Developer tools -> Assist** for a harmless one-turn question.
7. Ask a two-turn question and confirm context stays within that conversation.
8. Select device memory scope, start a new conversation on the same device, and
   confirm Hermes recalls an appropriate non-sensitive fact from the first one.
9. Confirm the same fact is not recalled from a different device until assistant
   scope is deliberately enabled.
10. Confirm a response ending in a question keeps the voice pipeline open.
11. Test an invalid API key and confirm Home Assistant starts reauthentication.
12. Stop the Hermes gateway and confirm Assist returns a bounded unavailable error.
13. Test from Voice PE with only read-only Hermes tools enabled.
14. Review Home Assistant and Hermes logs for secrets or full transcripts.
15. Enable mutating Home Assistant tools only after verifying their entity scope.
