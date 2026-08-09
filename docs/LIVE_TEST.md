# Live rollout checklist

1. Confirm `curl` from the Home Assistant host authenticates to
   `http://hermes.example-tailnet.ts.net:8642/v1/capabilities`.
2. Add Hermes Assistant in Home Assistant and confirm it loads without warnings.
3. Use **Developer tools -> Assist** for a harmless one-turn question.
4. Ask a two-turn question and confirm context stays within that conversation.
5. Select device memory scope, start a new conversation on the same device, and
   confirm Hermes recalls an appropriate non-sensitive fact from the first one.
6. Confirm the same fact is not recalled from a different device until assistant
   scope is deliberately enabled.
7. Confirm a response ending in a question keeps the voice pipeline open.
8. Test an invalid API key and confirm Home Assistant starts reauthentication.
9. Stop the Hermes gateway and confirm Assist returns a bounded unavailable error.
10. Test from Voice PE with only read-only Hermes tools enabled.
11. Review Home Assistant and Hermes logs for secrets or full transcripts.
12. Enable mutating Home Assistant tools only after verifying their entity scope.
