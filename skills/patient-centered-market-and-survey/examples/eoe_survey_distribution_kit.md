# EoE Survey — Distribution Kit

## A. Fastest path to a live anonymous form

1. Open **https://script.google.com** → **New project**.
2. Paste the contents of `build_EoE_form.gs`, click **Save**, click **Run**.
3. Approve the one-time permission prompt.
4. In the **Execution log**, copy the **LIVE FORM** URL — that's the anonymous link to share.

The script already sets: email collection **off**, one-response-per-user **off** (no forced sign-in), progress bar **on**. Nothing identifying is stored.

*Manual alternative:* build it by hand from `EoE_tolerizing_vaccine_survey.md` in Google Forms, then in **Settings → Responses** turn OFF "Collect email addresses" and "Limit to 1 response."

---

## B. Recruitment message (paste with the link)

**Short version (texts / group chats / stories):**

> Hi! I'm working on a hackathon project about a *new* kind of EoE treatment and I'd love input from people who actually live with it. It's a quick, fully anonymous survey (~5 min, one optional written question). Would mean a lot if you could fill it out **by end of day Saturday July 11** 🙏
> [LINK]

**Longer version (EoE Facebook / Reddit / Discord communities):**

> Hi everyone — I have EoE and I'm taking part in a life-sciences hackathon exploring a treatment idea that would retrain the immune system to *tolerate* trigger foods (instead of lifelong diet restriction or daily meds). To ground the idea in real patient experience, I put together a short anonymous survey: ~5 minutes, almost all multiple choice, one optional short-answer at the end. No names or emails are collected.
>
> If you have EoE, your perspective would genuinely help. I'm collecting responses **through end of day Saturday, July 11**. Thank you! 💙
> [LINK]

*Tip:* if you post in patient communities, check the group's rules first — some require mod approval for surveys. A quick "mods, happy to remove if not allowed" note helps.

---

## C. When responses come in

In the form, click **Responses → the green Sheets icon** to open the results spreadsheet, then **File → Download → CSV**. Save it as `eoe_survey_responses.csv`. Bring that CSV back here and load the **`eoe-survey-analysis`** skill — it will produce the summary charts and a report for your submission automatically.
