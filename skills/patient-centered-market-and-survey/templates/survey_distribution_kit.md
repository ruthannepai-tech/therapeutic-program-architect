# {Condition} Survey — Distribution Kit

## A. Fastest path to a live anonymous form
1. Open **https://script.google.com** → **New project**.
2. Paste the contents of `build_form.gs` (from `generate_form_script()`), **Save**, **Run** `buildForm`.
3. Approve the one-time permission prompt.
4. In the **Execution log**, copy the **LIVE FORM** url — that's the anonymous link to share.

The script sets email collection **off**, one-response-per-user **off** (no forced sign-in), progress bar **on**. Nothing identifying is stored.

*Manual alternative:* build by hand in Google Forms from the survey blueprint, then **Settings → Responses** → turn OFF "Collect email addresses" and "Limit to 1 response."

---

## B. Recruitment message (paste with the link)

**Short (texts / group chats / stories):**
> Hi! I'm working on a project about a new approach to {condition} and I'd love input from people who actually live with it. It's a quick, fully anonymous survey (~5 min, one optional written question). Would mean a lot if you could fill it out **by {deadline}** 🙏
> [LINK]

**Longer (patient Facebook / Reddit / Discord communities):**
> Hi everyone — I have {condition} and I'm exploring a treatment idea that would {one-line plain-language mechanism}. To ground it in real patient experience, I put together a short anonymous survey: ~5 minutes, almost all multiple choice, one optional short-answer at the end. No names or emails are collected.
>
> If you have {condition}, your perspective would genuinely help. I'm collecting responses **through {deadline}**. Thank you! 💙
> [LINK]

*Etiquette:* check each community's rules first — some require mod approval for surveys. A "mods, happy to remove if not allowed" note helps.

---

## C. When responses come in
In the form: **Responses → green Sheets icon** → **File → Download → CSV**. Save as `survey_responses.csv` and hand off to a survey-analysis step for summary charts and a report.
