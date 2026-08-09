# Live rollout checklist

1. Confirm `curl` from the Home Assistant host authenticates to
   `http://hermes.example-tailnet.ts.net:8642/v1/capabilities`.
2. Add Hermes Assistant in Home Assistant and confirm it loads without warnings.
3. Use **Developer tools -> Assist** for a harmless one-turn question.
4. Ask a two-turn question and confirm context stays within that conversation.
5. Confirm a response ending in a question keeps the voice pipeline open.
6. Test an invalid API key and confirm Home Assistant starts reauthentication.
7. Stop the Hermes gateway and confirm Assist returns a bounded unavailable error.
8. Test from Voice PE with only read-only Hermes tools enabled.
9. Review Home Assistant and Hermes logs for secrets or full transcripts.
10. Enable mutating Home Assistant tools only after verifying their entity scope.
