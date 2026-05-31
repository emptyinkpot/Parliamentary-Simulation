using System;
using System.Collections.Generic;
using UnityEngine;

/// Diplomatic relations, actions, alliances, and treaties between countries
public static class DiplomacySystem
{
    // --- Constants ---

    public const int MinRelation = -200;
    public const int MaxRelation = 200;

    // --- Data Structures ---

    [Serializable]
    public class RelationData
    {
        public int CountryA;
        public int CountryB;
        public int Value; // -200 to +200
        public DiplomaticRelation Level => GetLevel(Value);
    }

    [Serializable]
    public class Treaty
    {
        public int Id;
        public int CountryA;
        public int CountryB;
        public TreatyType Type;
        public DateTime SignedDate;
        public DateTime? ExpiryDate;
        public bool IsActive;
    }

    // --- Storage ---

    public static Dictionary<(int, int), RelationData> Relations = new();
    public static List<Treaty> Treaties = new();
    private static int _nextTreatyId = 1;

    // --- Relation Helpers ---

    public static DiplomaticRelation GetLevel(int value)
    {
        if (value >= 100) return DiplomaticRelation.Alliance;
        if (value >= 30) return DiplomaticRelation.Friendly;
        if (value >= -30) return DiplomaticRelation.Neutral;
        if (value >= -100) return DiplomaticRelation.Rival;
        return DiplomaticRelation.Hostile;
    }
    // --- Relation Access ---

    public static (int, int) Key(int a, int b) => a < b ? (a, b) : (b, a);

    public static int GetRelationValue(int countryA, int countryB)
    {
        var key = Key(countryA, countryB);
        return Relations.TryGetValue(key, out var r) ? r.Value : 0;
    }

    public static void SetRelation(int countryA, int countryB, int value)
    {
        var key = Key(countryA, countryB);
        if (!Relations.TryGetValue(key, out var r))
        {
            r = new RelationData { CountryA = key.Item1, CountryB = key.Item2 };
            Relations[key] = r;
        }
        r.Value = Mathf.Clamp(value, MinRelation, MaxRelation);
    }

    public static void ModifyRelation(int countryA, int countryB, int delta)
    {
        int current = GetRelationValue(countryA, countryB);
        SetRelation(countryA, countryB, current + delta);
    }

    // --- Diplomatic Actions ---

    public static void PerformAction(int actor, int target, DiplomaticAction action)
    {
        switch (action)
        {
            case DiplomaticAction.ImproveRelations:
                ModifyRelation(actor, target, 15);
                break;
            case DiplomaticAction.Insult:
                ModifyRelation(actor, target, -30);
                break;
            case DiplomaticAction.Warn:
                ModifyRelation(actor, target, -10);
                break;
            case DiplomaticAction.GuaranteeIndependence:
                ModifyRelation(actor, target, 20);
                break;
            case DiplomaticAction.DeclareWar:
                ModifyRelation(actor, target, -100);
                break;
            case DiplomaticAction.OfferPeace:
                ModifyRelation(actor, target, 25);
                break;
        }
    }
    // --- Alliance ---

    /// Check if two countries are in a military alliance (mutual defense).
    public static bool AreAllied(int countryA, int countryB)
    {
        foreach (var t in Treaties)
        {
            if (!t.IsActive) continue;
            if (t.Type != TreatyType.MilitaryAlliance && t.Type != TreatyType.DefensivePact) continue;
            var key = Key(t.CountryA, t.CountryB);
            if (key == Key(countryA, countryB)) return true;
        }
        return false;
    }

    // --- Treaties ---

    public static Treaty CreateTreaty(int countryA, int countryB, TreatyType type, int durationMonths = 0)
    {
        var treaty = new Treaty
        {
            Id = _nextTreatyId++,
            CountryA = countryA,
            CountryB = countryB,
            Type = type,
            SignedDate = DateTime.Now,
            ExpiryDate = durationMonths > 0 ? DateTime.Now.AddMonths(durationMonths) : null,
            IsActive = true
        };
        Treaties.Add(treaty);
        ModifyRelation(countryA, countryB, 30);
        return treaty;
    }

    public static void ExpireTreaties()
    {
        var now = DateTime.Now;
        foreach (var t in Treaties)
        {
            if (t.IsActive && t.ExpiryDate.HasValue && now >= t.ExpiryDate.Value)
                t.IsActive = false;
        }
    }
    // --- Initial 11 Countries Setup ---

    /// Country IDs: JPN=1, CHN=2, KOR=3, RUS=4, GBR=5, FRA=6, DEU=7, USA=8, OTT=9, AUH=10, ITA=11
    public static void InitializeDefaultRelations()
    {
        Relations.Clear();
        // Japan's starting relations
        SetRelation(1, 5, 50);   // JPN-GBR: Friendly (Anglo-Japanese Alliance)
        SetRelation(1, 4, -60);  // JPN-RUS: Rival
        SetRelation(1, 2, -40);  // JPN-CHN: Rival
        SetRelation(1, 3, -80);  // JPN-KOR: Hostile (colonial tension)
        SetRelation(1, 7, 20);   // JPN-DEU: Slightly positive
        SetRelation(1, 8, 10);   // JPN-USA: Neutral-positive
        SetRelation(1, 6, 15);   // JPN-FRA: Neutral-positive
        // European relations
        SetRelation(5, 6, 40);   // GBR-FRA: Friendly (Entente Cordiale)
        SetRelation(5, 7, -50);  // GBR-DEU: Rival (naval race)
        SetRelation(6, 4, 60);   // FRA-RUS: Friendly (Franco-Russian Alliance)
        SetRelation(6, 7, -70);  // FRA-DEU: Rival
        SetRelation(7, 10, 80);  // DEU-AUH: Allied (Dual Alliance)
        SetRelation(7, 9, 30);   // DEU-OTT: Friendly
        SetRelation(4, 9, -50);  // RUS-OTT: Rival
        SetRelation(10, 9, -30); // AUH-OTT: Rival (Balkans)
        SetRelation(10, 4, -40); // AUH-RUS: Rival (Balkans)
        // Weak powers
        SetRelation(2, 5, -60);  // CHN-GBR: Rival (Opium Wars legacy)
        SetRelation(2, 4, -30);  // CHN-RUS: Rival (Manchuria)
    }
}
