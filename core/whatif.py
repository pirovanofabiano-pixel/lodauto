def what_if_simulation(df, budget_dict, baseline_budget=3000):
    results = []

    for fonte, budget_sim in budget_dict.items():
        storico = df[df["fonte"] == fonte]

        if storico.empty:
            continue

        lead_medio = storico.groupby("mese").size().mean()
        vendite_medie = storico.groupby("mese")["is_deal"].sum().mean()

        fattore = budget_sim / baseline_budget

        results.append({
            "Fonte": fonte,
            "Budget simulato (€)": budget_sim,
            "Lead stimati": int(lead_medio * fattore),
            "Vendite stimate": int(vendite_medie * fattore)
        })

    return results