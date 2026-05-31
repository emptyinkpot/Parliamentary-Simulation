using System;
using System.Collections.Generic;
using UnityEngine;

/// War declaration, war goals, war score, peace negotiation, and state machine
public static class WarSystem
{
    // --- Data Structures ---

    [Serializable]
    public class WarGoal
    {
        public enum GoalType { Territory, Reparations, Vassalization }
        public GoalType Type;
        public int TargetProvinceId; // for Territory goals
        public float ReparationAmount; // for Reparations goals
    }

    [Serializable]
    public class War
    {
        public int Id;
        public string Name;
        public int AttackerCountryId;
        public int DefenderCountryId;
        public CasusBelli CasusBelli;
        public WarStatus Status;
        public List<WarGoal> AttackerGoals = new();
        public List<WarGoal> DefenderGoals = new();
        public int BattlesWonByAttacker;
        public int BattlesWonByDefender;
        public int ProvincesOccupiedByAttacker;
        public int ProvincesOccupiedByDefender;
        public int BlockadeScore;
        public int MonthsAtWar;
        public DateTime StartDate;
    }

    // --- Storage ---

    public static Dictionary<int, War> ActiveWars = new();
    private static int _nextWarId = 1;

    // --- War Declaration ---

    /// Declare war. A casus belli is required. Returns the new War or null on failure.
    public static War DeclareWar(int attackerId, int defenderId, CasusBelli cb, string warName = null)
    {
        if (attackerId == defenderId) return null;

        var war = new War
        {
            Id = _nextWarId++,
            Name = warName ?? $"War #{_nextWarId - 1}",
            AttackerCountryId = attackerId,
            DefenderCountryId = defenderId,
            CasusBelli = cb,
            Status = WarStatus.Preparing,
            StartDate = DateTime.Now
        };
        ActiveWars[war.Id] = war;
        return war;
    }

    /// Transition war from Preparing to Active.
    public static bool ActivateWar(int warId)
    {
        if (!ActiveWars.TryGetValue(warId, out var war)) return false;
        if (war.Status != WarStatus.Preparing) return false;
        war.Status = WarStatus.Active;
        return true;
    }

    // --- War Score ---

    /// Calculate war score for the attacker (0-100). Defender score = 100 - attacker score.
    public static float CalculateWarScore(War war)
    {
        float battleScore = (war.BattlesWonByAttacker - war.BattlesWonByDefender) * 10f;
        float occupationScore = (war.ProvincesOccupiedByAttacker - war.ProvincesOccupiedByDefender) * 5f;
        float blockadeBonus = war.BlockadeScore * 2f;
        return Mathf.Clamp(50f + battleScore + occupationScore + blockadeBonus, 0f, 100f);
    }

    /// Record a battle result into the war.
    public static void RecordBattle(int warId, bool attackerWon)
    {
        if (!ActiveWars.TryGetValue(warId, out var war)) return;
        if (attackerWon) war.BattlesWonByAttacker++;
        else war.BattlesWonByDefender++;
    }

    // --- Peace Negotiation ---

    /// Begin peace negotiations. Transitions Active -> Negotiating.
    public static bool BeginNegotiation(int warId)
    {
        if (!ActiveWars.TryGetValue(warId, out var war)) return false;
        if (war.Status != WarStatus.Active) return false;
        war.Status = WarStatus.Negotiating;
        return true;
    }

    /// Check if a set of demands is acceptable given the current war score.
    /// Each demand costs score: Territory=10, Reparations=5, Vassalization=50.
    public static bool CanDemand(War war, List<WarGoal> demands)
    {
        float score = CalculateWarScore(war);
        float cost = 0f;
        foreach (var d in demands)
        {
            switch (d.Type)
            {
                case WarGoal.GoalType.Territory: cost += 10f; break;
                case WarGoal.GoalType.Reparations: cost += 5f; break;
                case WarGoal.GoalType.Vassalization: cost += 50f; break;
            }
        }
        return score >= cost;
    }

    /// Sign peace and end the war. Returns false if not in Negotiating state.
    public static bool SignPeace(int warId)
    {
        if (!ActiveWars.TryGetValue(warId, out var war)) return false;
        if (war.Status != WarStatus.Negotiating) return false;
        war.Status = WarStatus.Ended;
        return true;
    }
}
