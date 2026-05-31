using System;
using System.Collections.Generic;
using System.Linq;
using UnityEngine;
using ImperialStrategy.Events;

/// Event system: definitions, triggers, chains, random pools, and effects.
public static class EventSystem
{
    // --- Data Structures ---

    [System.Serializable]
    public struct EventOption
    {
        public string Text;
        public List<EventEffect> Effects;
        public int ChainEventId; // -1 if none
    }

    [System.Serializable]
    public struct EventEffect
    {
        public string TargetType; // "country", "province"
        public int TargetId;
        public string Stat; // "treasury", "stability", "relations", etc.
        public float Delta;
    }

    [System.Serializable]
    public struct EventDefinition
    {
        public int Id;
        public string Title;
        public string Description;
        public EventType Type;
        public EventImportance Importance;
        public EventTriggerType TriggerType;
        public List<EventOption> Options;
        // Trigger conditions
        public int TriggerDay; // for DateBased
        public Func<bool> Condition; // for ConditionBased
        public float Weight; // for Random pool
        public int ChainParentId; // for ChainEvent, -1 if root
    }

    [System.Serializable]
    public struct ActiveEvent
    {
        public int DefinitionId;
        public int TargetCountryId;
        public bool Resolved;
    }

    // --- State ---

    private static Dictionary<int, EventDefinition> _definitions = new();
    private static List<ActiveEvent> _activeEvents = new();
    private static int _nextId = 1;
    private static int _currentDay = 0;

    // --- Public API ---

    /// Register a new event definition. Returns assigned ID.
    public static int RegisterEvent(
        string title, string description,
        EventType type, EventImportance importance,
        EventTriggerType triggerType,
        List<EventOption> options,
        int triggerDay = -1,
        Func<bool> condition = null,
        float weight = 1f,
        int chainParentId = -1)
    {
        int id = _nextId++;
        _definitions[id] = new EventDefinition
        {
            Id = id,
            Title = title,
            Description = description,
            Type = type,
            Importance = importance,
            TriggerType = triggerType,
            Options = options ?? new List<EventOption>(),
            TriggerDay = triggerDay,
            Condition = condition,
            Weight = weight,
            ChainParentId = chainParentId
        };
        return id;
    }

    /// Advance the day counter and check for triggered events.
    public static List<ActiveEvent> Tick(int countryId)
    {
        _currentDay++;
        var triggered = new List<ActiveEvent>();

        foreach (var kvp in _definitions)
        {
            var def = kvp.Value;
            bool shouldFire = def.TriggerType switch
            {
                EventTriggerType.DateBased => def.TriggerDay == _currentDay,
                EventTriggerType.ConditionBased => def.Condition != null && def.Condition(),
                EventTriggerType.Random => ShouldFireRandom(def.Weight),
                EventTriggerType.ChainEvent => false, // fired manually
                _ => false
            };

            if (shouldFire)
            {
                var active = new ActiveEvent
                {
                    DefinitionId = def.Id,
                    TargetCountryId = countryId,
                    Resolved = false
                };
                _activeEvents.Add(active);
                triggered.Add(active);
            }
        }
        return triggered;
    }

    /// Resolve an active event by choosing an option index. Applies effects and fires chain events.
    public static void ResolveEvent(int activeEventIndex, int optionIndex)
    {
        if (activeEventIndex < 0 || activeEventIndex >= _activeEvents.Count)
            return;

        var active = _activeEvents[activeEventIndex];
        if (active.Resolved) return;

        if (!_definitions.TryGetValue(active.DefinitionId, out var def))
            return;

        if (optionIndex < 0 || optionIndex >= def.Options.Count)
            return;

        var option = def.Options[optionIndex];

        // Apply effects
        foreach (var effect in option.Effects)
            ApplyEffect(effect);

        // Fire chain event if specified
        if (option.ChainEventId > 0)
            FireChainEvent(option.ChainEventId, active.TargetCountryId);

        active.Resolved = true;
        _activeEvents[activeEventIndex] = active;
    }

    /// Manually fire a chain event for a country.
    public static void FireChainEvent(int eventId, int countryId)
    {
        if (!_definitions.ContainsKey(eventId)) return;
        _activeEvents.Add(new ActiveEvent
        {
            DefinitionId = eventId,
            TargetCountryId = countryId,
            Resolved = false
        });
    }

    /// Pick a random event from the pool using weighted selection.
    public static int? PickRandomEvent()
    {
        var pool = _definitions.Values
            .Where(d => d.TriggerType == EventTriggerType.Random)
            .ToList();
        if (pool.Count == 0) return null;

        float totalWeight = pool.Sum(d => d.Weight);
        float roll = UnityEngine.Random.Range(0f, totalWeight);
        float cumulative = 0f;
        foreach (var def in pool)
        {
            cumulative += def.Weight;
            if (roll <= cumulative)
                return def.Id;
        }
        return pool.Last().Id;
    }

    public static List<ActiveEvent> GetUnresolvedEvents()
    {
        return _activeEvents.Where(e => !e.Resolved).ToList();
    }

    public static EventDefinition? GetDefinition(int id)
    {
        return _definitions.TryGetValue(id, out var def) ? def : null;
    }

    public static int CurrentDay => _currentDay;

    // --- Private Helpers ---

    private static bool ShouldFireRandom(float weight)
    {
        // Base 1% chance per day, scaled by weight
        return UnityEngine.Random.value < 0.01f * weight;
    }

    private static void ApplyEffect(EventEffect effect)
    {
        switch (effect.TargetType)
        {
            case "country":
                if (CountryData.All.TryGetValue(effect.TargetId, out var country))
                {
                    if (effect.Stat == "treasury")
                        country.Treasury += effect.Delta;
                }
                break;
            case "province":
                if (ProvinceData.IdLookup.TryGetValue(effect.TargetId, out var prov))
                {
                    if (effect.Stat == "population")
                        prov.Population += Mathf.RoundToInt(effect.Delta);
                    else if (effect.Stat == "tax")
                        prov.Tax += effect.Delta;
                }
                break;
        }
    }
}
