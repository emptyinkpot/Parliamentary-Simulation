namespace ImperialStrategy.Events
{
    public enum EventType
    {
        Political,
        Economic,
        Military,
        Diplomatic,
        Social,
        Cultural,
        Natural,
        Religious,
        Scientific,
        Colonial,
        Faction,
        Imperial
    }

    public enum EventImportance
    {
        Trivial,
        Minor,
        Normal,
        Major,
        Critical
    }

    public enum EventTriggerType
    {
        DateBased,
        ConditionBased,
        Random,
        ChainEvent
    }
}
