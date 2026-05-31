using System;
using System.Collections.Generic;
using System.Linq;

/// Achievement tracking: rarity tiers, conditions, progress, unlock notifications.
public static class AchievementSystem
{
    // --- Enums ---

    public enum AchievementRarity
    {
        Common,
        Rare,
        Epic,
        Legendary
    }

    public enum AchievementConditionType
    {
        OwnProvinces,
        WinWars,
        ReachGDP,
        CollectTax,
        BuildBuildings,
        TradeRoutes,
        PopulationTotal
    }

    // --- Data Structures ---

    [System.Serializable]
    public struct AchievementDefinition
    {
        public int Id;
        public string Name;
        public string Description;
        public AchievementRarity Rarity;
        public AchievementConditionType ConditionType;
        public float Threshold;
    }

    [System.Serializable]
    public struct AchievementProgress
    {
        public int AchievementId;
        public int CountryId;
        public float CurrentValue;
        public bool Unlocked;
        public int UnlockedOnDay;
    }

    // --- State ---

    private static Dictionary<int, AchievementDefinition> _definitions = new();
    private static List<AchievementProgress> _progress = new();
    private static int _nextId = 1;

    /// Callback fired when an achievement is unlocked. (AchievementId, CountryId)
    public static Action<int, int> OnAchievementUnlocked;

    // --- Public API ---

    /// Register a new achievement definition. Returns assigned ID.
    public static int Register(string name, string description, AchievementRarity rarity,
        AchievementConditionType conditionType, float threshold)
    {
        int id = _nextId++;
        _definitions[id] = new AchievementDefinition
        {
            Id = id,
            Name = name,
            Description = description,
            Rarity = rarity,
            ConditionType = conditionType,
            Threshold = threshold
        };
        return id;
    }

    /// Check all achievements for a country and update progress.
    public static List<int> CheckProgress(int countryId, int currentDay)
    {
        var newlyUnlocked = new List<int>();

        foreach (var kvp in _definitions)
        {
            var def = kvp.Value;
            float currentValue = EvaluateCondition(countryId, def.ConditionType);

            int idx = _progress.FindIndex(p => p.AchievementId == def.Id && p.CountryId == countryId);
            if (idx >= 0)
            {
                var prog = _progress[idx];
                if (prog.Unlocked) continue;
                prog.CurrentValue = currentValue;
                if (currentValue >= def.Threshold)
                {
                    prog.Unlocked = true;
                    prog.UnlockedOnDay = currentDay;
                    newlyUnlocked.Add(def.Id);
                    OnAchievementUnlocked?.Invoke(def.Id, countryId);
                }
                _progress[idx] = prog;
            }
            else
            {
                bool unlocked = currentValue >= def.Threshold;
                _progress.Add(new AchievementProgress
                {
                    AchievementId = def.Id,
                    CountryId = countryId,
                    CurrentValue = currentValue,
                    Unlocked = unlocked,
                    UnlockedOnDay = unlocked ? currentDay : -1
                });
                if (unlocked)
                {
                    newlyUnlocked.Add(def.Id);
                    OnAchievementUnlocked?.Invoke(def.Id, countryId);
                }
            }
        }
        return newlyUnlocked;
    }

    /// Get progress percentage for a specific achievement (0-100).
    public static float GetProgressPercent(int achievementId, int countryId)
    {
        if (!_definitions.TryGetValue(achievementId, out var def))
            return 0f;
        var prog = _progress.FirstOrDefault(p => p.AchievementId == achievementId && p.CountryId == countryId);
        if (def.Threshold <= 0f) return 100f;
        return UnityEngine.Mathf.Clamp(prog.CurrentValue / def.Threshold * 100f, 0f, 100f);
    }

    /// Get all unlocked achievements for a country.
    public static List<AchievementDefinition> GetUnlocked(int countryId)
    {
        var unlockedIds = _progress
            .Where(p => p.CountryId == countryId && p.Unlocked)
            .Select(p => p.AchievementId)
            .ToHashSet();
        return _definitions.Values.Where(d => unlockedIds.Contains(d.Id)).ToList();
    }

    /// Get all achievement definitions.
    public static IReadOnlyList<AchievementDefinition> GetAllDefinitions()
    {
        return _definitions.Values.ToList();
    }

    /// Check if a specific achievement is unlocked.
    public static bool IsUnlocked(int achievementId, int countryId)
    {
        return _progress.Any(p => p.AchievementId == achievementId && p.CountryId == countryId && p.Unlocked);
    }

    // --- Private Helpers ---

    private static float EvaluateCondition(int countryId, AchievementConditionType conditionType)
    {
        if (!CountryData.All.TryGetValue(countryId, out var country))
            return 0f;

        switch (conditionType)
        {
            case AchievementConditionType.OwnProvinces:
                return country.OwnedProvinceIds.Count;

            case AchievementConditionType.ReachGDP:
                return EconomySystem.CalculateGDP(country);

            case AchievementConditionType.PopulationTotal:
                int pop = 0;
                foreach (int pid in country.OwnedProvinceIds)
                    if (ProvinceData.IdLookup.TryGetValue(pid, out var prov))
                        pop += prov.Population;
                return pop;

            case AchievementConditionType.CollectTax:
                return country.Treasury;

            case AchievementConditionType.WinWars:
                // Placeholder: tracked externally
                return 0f;

            case AchievementConditionType.BuildBuildings:
                int buildings = 0;
                foreach (int pid in country.OwnedProvinceIds)
                    buildings += BuildingSystem.GetBuildings(pid).Count;
                return buildings;

            case AchievementConditionType.TradeRoutes:
                return TradeSystem.GetRoutesForCountry(countryId).Count;

            default:
                return 0f;
        }
    }
}
