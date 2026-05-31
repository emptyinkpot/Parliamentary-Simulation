using System.Collections.Generic;
using System.Linq;
using UnityEngine;
using ImperialStrategy.Economy;

/// Comprehensive economy simulation: GDP, taxes, budget, inflation, unemployment, zaibatsu influence.
public static class EconomySystem
{
    // --- Country-level economic state ---
    public struct EconomicState
    {
        public float GDP;
        public float GDPGrowth;
        public float Inflation;
        public float Unemployment;
        public float MoneySupply;
        public float GoodsOutput;
        public float TaxRate;
        public float NationalDebt;
        public Dictionary<BudgetCategory, float> BudgetAllocation;
    }

    private static Dictionary<int, EconomicState> _states = new();

    // --- Configuration ---
    private const float BaseTaxRate = 0.10f;
    private const float BaseInflationThreshold = 1.2f;
    private const float DeflationThreshold = 0.8f;
    private const float BaseUnemploymentRate = 0.04f;
    private const float ZaibatsuInfluenceCap = 0.30f;

    // --- Public API ---

    public static EconomicState GetState(int countryId)
    {
        if (_states.TryGetValue(countryId, out var state))
            return state;
        return InitState(countryId);
    }

    public static void SetTaxRate(int countryId, float rate)
    {
        var state = GetState(countryId);
        state.TaxRate = Mathf.Clamp01(rate);
        _states[countryId] = state;
    }

    public static void SetBudgetAllocation(int countryId, Dictionary<BudgetCategory, float> allocation)
    {
        var state = GetState(countryId);
        state.BudgetAllocation = NormalizeBudget(allocation);
        _states[countryId] = state;
    }

    /// Monthly tick: collect taxes, pay expenses, update indicators.
    public static void Tick()
    {
        foreach (var country in CountryData.All.Values)
        {
            var state = GetState(country.Id);

            float taxIncome = CalculateTaxCollection(country, state.TaxRate);
            float gdp = CalculateGDP(country);
            float expenses = CalculateExpenses(country, state);

            country.Treasury += taxIncome - expenses;
            state.GDP = gdp;
            state.GDPGrowth = gdp > 0 ? (taxIncome - expenses) / gdp : 0f;
            state.MoneySupply += taxIncome;
            state.GoodsOutput = gdp * 0.6f;
            state.Inflation = CalculateInflation(state);
            state.Unemployment = CalculateUnemployment(country, state);

            _states[country.Id] = state;
        }
    }

    // --- GDP Calculation ---

    public static float CalculateGDP(CountryData country)
    {
        float total = 0f;
        foreach (int pid in country.OwnedProvinceIds)
        {
            if (ProvinceData.IdLookup.TryGetValue(pid, out var prov))
                total += GetProvinceOutput(prov);
        }
        return total;
    }

    // --- Tax Collection ---

    public static float CalculateTaxCollection(CountryData country, float taxRate)
    {
        float total = 0f;
        foreach (int pid in country.OwnedProvinceIds)
        {
            if (ProvinceData.IdLookup.TryGetValue(pid, out var prov))
                total += prov.Population * prov.Tax * taxRate;
        }
        return total;
    }

    // --- Budget Allocation ---

    public static Dictionary<BudgetCategory, float> GetBudgetSpending(int countryId, float totalIncome)
    {
        var state = GetState(countryId);
        var spending = new Dictionary<BudgetCategory, float>();
        foreach (var kvp in state.BudgetAllocation)
            spending[kvp.Key] = totalIncome * kvp.Value;
        return spending;
    }

    // --- Inflation / Deflation ---

    public static float CalculateInflation(EconomicState state)
    {
        if (state.GoodsOutput <= 0f) return 0f;
        float ratio = state.MoneySupply / state.GoodsOutput;
        if (ratio > BaseInflationThreshold)
            return (ratio - BaseInflationThreshold) * 10f;
        if (ratio < DeflationThreshold)
            return (ratio - DeflationThreshold) * 10f;
        return 0f;
    }

    // --- Unemployment ---

    public static float CalculateUnemployment(CountryData country, EconomicState state)
    {
        int totalPop = 0;
        int employedEstimate = 0;
        foreach (int pid in country.OwnedProvinceIds)
        {
            if (ProvinceData.IdLookup.TryGetValue(pid, out var prov))
            {
                totalPop += prov.Population;
                employedEstimate += Mathf.RoundToInt(prov.Population * (1f - BaseUnemploymentRate));
            }
        }
        if (totalPop == 0) return 0f;
        float baseRate = 1f - (float)employedEstimate / totalPop;
        // High inflation increases unemployment
        float inflationPenalty = Mathf.Max(0f, state.Inflation * 0.01f);
        return Mathf.Clamp01(baseRate + inflationPenalty);
    }

    // --- Zaibatsu / Corporation Influence ---

    /// Returns political influence modifier from zaibatsu presence (0..ZaibatsuInfluenceCap).
    public static float GetZaibatsuInfluence(int countryId, float totalZaibatsuAssets)
    {
        var state = GetState(countryId);
        if (state.GDP <= 0f) return 0f;
        float ratio = totalZaibatsuAssets / state.GDP;
        return Mathf.Clamp(ratio, 0f, ZaibatsuInfluenceCap);
    }

    // --- Private Helpers ---

    private static EconomicState InitState(int countryId)
    {
        var state = new EconomicState
        {
            GDP = 0f,
            GDPGrowth = 0f,
            Inflation = 0f,
            Unemployment = BaseUnemploymentRate,
            MoneySupply = 100f,
            GoodsOutput = 100f,
            TaxRate = BaseTaxRate,
            NationalDebt = 0f,
            BudgetAllocation = DefaultBudget()
        };
        _states[countryId] = state;
        return state;
    }

    private static Dictionary<BudgetCategory, float> DefaultBudget()
    {
        return new Dictionary<BudgetCategory, float>
        {
            { BudgetCategory.Military, 0.30f },
            { BudgetCategory.Administration, 0.20f },
            { BudgetCategory.Construction, 0.20f },
            { BudgetCategory.Research, 0.15f },
            { BudgetCategory.Welfare, 0.15f }
        };
    }

    private static Dictionary<BudgetCategory, float> NormalizeBudget(Dictionary<BudgetCategory, float> raw)
    {
        float sum = raw.Values.Sum();
        if (sum <= 0f) return DefaultBudget();
        var result = new Dictionary<BudgetCategory, float>();
        foreach (var kvp in raw)
            result[kvp.Key] = kvp.Value / sum;
        return result;
    }

    private static float GetProvinceOutput(ProvinceData prov)
    {
        return prov.Population * prov.Tax * 1.5f;
    }

    private static float CalculateExpenses(CountryData country, EconomicState state)
    {
        float income = CalculateTaxCollection(country, state.TaxRate);
        return income * 0.85f; // 85% of income goes to expenses
    }
}
