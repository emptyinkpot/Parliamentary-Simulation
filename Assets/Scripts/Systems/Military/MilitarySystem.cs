using System;
using System.Collections.Generic;
using UnityEngine;

/// Army/Navy management, recruitment, movement, battle, siege, and war exhaustion
public static class MilitarySystem
{
    // --- Data Structures ---

    [Serializable]
    public class Army
    {
        public int Id;
        public int OwnerCountryId;
        public int ProvinceId;
        public int Strength;
        public float Morale;       // 0-100
        public float Supply;       // 0-100
        public string LeaderName;
        public float LeaderBonus;  // 0-1 multiplier
        public MilitaryBranch Branch;
    }

    [Serializable]
    public class BattleResult
    {
        public int AttackerLosses;
        public int DefenderLosses;
        public bool AttackerWon;
        public float MoraleShiftAttacker;
        public float MoraleShiftDefender;
    }

    // --- Constants ---

    public const int BaseMovementDays = 1;
    public const float BaseMoraleRecovery = 2f;
    public const float WarExhaustionPerBattle = 5f;
    public const float WarExhaustionPerMonth = 0.5f;
    public const float SiegeBaseDaysPerLevel = 30f;

    // --- Storage ---

    public static Dictionary<int, Army> Armies = new();
    private static int _nextArmyId = 1;

    // --- Recruitment ---

    /// Recruit an army from a province's population.
    /// Returns null if province has insufficient population.
    public static Army Recruit(int ownerCountryId, int provinceId, int requestedStrength, MilitaryBranch branch, string leaderName = null)
    {
        if (!ProvinceData.IdLookup.TryGetValue(provinceId, out var province))
            return null;

        int available = province.Population / 10; // max 10% of population
        int strength = Mathf.Min(requestedStrength, available);
        if (strength <= 0) return null;

        province.Population -= strength;

        var army = new Army
        {
            Id = _nextArmyId++,
            OwnerCountryId = ownerCountryId,
            ProvinceId = provinceId,
            Strength = strength,
            Morale = 100f,
            Supply = 100f,
            LeaderName = leaderName,
            LeaderBonus = string.IsNullOrEmpty(leaderName) ? 0f : 0.1f,
            Branch = branch
        };
        Armies[army.Id] = army;
        return army;
    }

    // --- Movement ---

    /// Move army to an adjacent province. Returns travel days (terrain-modified).
    /// terrainModifier: 1.0 = flat, 1.5 = hills, 2.0 = mountains, 0.5 = road
    public static int MoveArmy(int armyId, int targetProvinceId, float terrainModifier = 1f)
    {
        if (!Armies.TryGetValue(armyId, out var army)) return -1;
        if (!ProvinceData.IdLookup.ContainsKey(targetProvinceId)) return -1;

        army.ProvinceId = targetProvinceId;
        army.Supply = Mathf.Max(0f, army.Supply - 5f);
        return Mathf.CeilToInt(BaseMovementDays * terrainModifier);
    }

    // --- Battle ---

    /// Resolve a battle between attacker and defender.
    /// terrainDefenseBonus: 0-0.5 extra multiplier for defender.
    public static BattleResult ResolveBattle(Army attacker, Army defender, float terrainDefenseBonus = 0f)
    {
        float atkPower = attacker.Strength * (attacker.Morale / 100f) * (1f + attacker.LeaderBonus);
        float defPower = defender.Strength * (defender.Morale / 100f) * (1f + defender.LeaderBonus + terrainDefenseBonus);

        float total = atkPower + defPower;
        if (total <= 0f) return new BattleResult();

        float atkRatio = atkPower / total;
        float defRatio = defPower / total;

        int atkLosses = Mathf.RoundToInt(attacker.Strength * defRatio * 0.3f);
        int defLosses = Mathf.RoundToInt(defender.Strength * atkRatio * 0.3f);

        attacker.Strength = Mathf.Max(0, attacker.Strength - atkLosses);
        defender.Strength = Mathf.Max(0, defender.Strength - defLosses);

        bool attackerWon = atkPower > defPower;
        float moraleSwing = 15f;

        attacker.Morale = Mathf.Clamp(attacker.Morale + (attackerWon ? moraleSwing * 0.5f : -moraleSwing), 0f, 100f);
        defender.Morale = Mathf.Clamp(defender.Morale + (attackerWon ? -moraleSwing : moraleSwing * 0.5f), 0f, 100f);

        return new BattleResult
        {
            AttackerLosses = atkLosses,
            DefenderLosses = defLosses,
            AttackerWon = attackerWon,
            MoraleShiftAttacker = attackerWon ? moraleSwing * 0.5f : -moraleSwing,
            MoraleShiftDefender = attackerWon ? -moraleSwing : moraleSwing * 0.5f
        };
    }

    // --- Siege ---

    /// Calculate siege duration in days based on fortress level (1-10).
    public static int GetSiegeDuration(int fortressLevel)
    {
        return Mathf.RoundToInt(SiegeBaseDaysPerLevel * Mathf.Max(1, fortressLevel));
    }

    /// Apply daily siege progress. Returns true when siege completes.
    public static bool AdvanceSiege(int fortressLevel, ref int daysBesieged)
    {
        daysBesieged++;
        return daysBesieged >= GetSiegeDuration(fortressLevel);
    }

    // --- War Exhaustion ---

    /// Calculate accumulated war exhaustion for a country.
    /// battlesCount: total battles fought. monthsAtWar: duration in months.
    public static float CalculateWarExhaustion(int battlesCount, int monthsAtWar)
    {
        return Mathf.Clamp(
            battlesCount * WarExhaustionPerBattle + monthsAtWar * WarExhaustionPerMonth,
            0f, 100f);
    }
}
