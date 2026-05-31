using System;
using System.Collections.Generic;
using UnityEngine;

/// Colony creation, monthly growth, management, and independence movements
public static class ColonySystem
{
    // --- Data Structures ---

    [Serializable]
    public class Colony
    {
        public int Id;
        public string Name;
        public int OwnerCountryId;
        public int ProvinceId;
        public float Progress;       // 0-100, colony development
        public string GovernorName;
        public float TaxRate;        // 0-1
        public float Autonomy;       // 0-100
        public float Unrest;         // 0-100
        public bool IndependenceMovement;
        public DateTime EstablishedDate;
    }

    // --- Constants ---

    public const int RequiredTechLevel = 3;
    public const int RequiredNavalPower = 20;
    public const float BaseMonthlyGrowth = 2f;
    public const float UnrestThreshold = 60f;
    public const float AutonomyThreshold = 30f;

    // --- Storage ---

    public static Dictionary<int, Colony> Colonies = new();
    private static int _nextColonyId = 1;

    // --- Colony Creation ---

    /// Create a colony. Requires tech level and naval power thresholds.
    /// Returns null if requirements not met.
    public static Colony CreateColony(string name, int ownerCountryId, int provinceId, int techLevel, int navalPower)
    {
        if (techLevel < RequiredTechLevel) return null;
        if (navalPower < RequiredNavalPower) return null;

        var colony = new Colony
        {
            Id = _nextColonyId++,
            Name = name,
            OwnerCountryId = ownerCountryId,
            ProvinceId = provinceId,
            Progress = 0f,
            TaxRate = 0.1f,
            Autonomy = 50f,
            Unrest = 0f,
            IndependenceMovement = false,
            EstablishedDate = DateTime.Now
        };
        Colonies[colony.Id] = colony;
        return colony;
    }

    // --- Monthly Tick ---

    /// Advance all colonies by one month: grow progress, update unrest.
    public static void MonthlyTick()
    {
        foreach (var colony in Colonies.Values)
        {
            // Progress growth (higher autonomy = slower growth for owner)
            float growthMod = 1f - (colony.Autonomy / 200f);
            colony.Progress = Mathf.Min(100f, colony.Progress + BaseMonthlyGrowth * growthMod);

            // Unrest increases with high tax and low autonomy
            float unrestDelta = (colony.TaxRate * 10f) - (colony.Autonomy * 0.05f);
            colony.Unrest = Mathf.Clamp(colony.Unrest + unrestDelta, 0f, 100f);

            // Independence movement trigger
            colony.IndependenceMovement = colony.Autonomy < AutonomyThreshold && colony.Unrest > UnrestThreshold;
        }
    }
    // --- Colony Management ---

    /// Assign a governor to a colony.
    public static void SetGovernor(int colonyId, string governorName)
    {
        if (Colonies.TryGetValue(colonyId, out var colony))
            colony.GovernorName = governorName;
    }

    /// Set colony tax rate (clamped 0-1).
    public static void SetTaxRate(int colonyId, float rate)
    {
        if (Colonies.TryGetValue(colonyId, out var colony))
            colony.TaxRate = Mathf.Clamp01(rate);
    }

    /// Set colony autonomy level (clamped 0-100).
    public static void SetAutonomy(int colonyId, float autonomy)
    {
        if (Colonies.TryGetValue(colonyId, out var colony))
            colony.Autonomy = Mathf.Clamp(autonomy, 0f, 100f);
    }

    /// Check if a colony has an active independence movement.
    public static bool HasIndependenceMovement(int colonyId)
    {
        return Colonies.TryGetValue(colonyId, out var colony) && colony.IndependenceMovement;
    }

    /// Grant independence: removes colony from owner's control.
    public static bool GrantIndependence(int colonyId)
    {
        if (!Colonies.TryGetValue(colonyId, out var colony)) return false;
        Colonies.Remove(colonyId);
        return true;
    }
}
