package gov.nist.oar.customizationapi.exceptions;

public class InvalidInputException extends Exception{

    /**
     * 
     */
    private static final long serialVersionUID = -3549633360117422045L;

    /**
     * Create an exception with an arbitrary message
     */
    public InvalidInputException(String msg) { super(msg); }

    /**
     * Create an exception with an arbitrary message and an underlying cause
     */
    public InvalidInputException(String msg, Throwable cause) { super(msg, cause); }

    /**
     * Create an exception with an underlying cause.  A default message is created.
     */
    public InvalidInputException(Throwable cause) { super(messageFor(cause), cause); }

    /**
     * return a message prefix that can introduce a more specific message
     */
    public static String getMessagePrefix() {
        return "Customization API exception encountered while processing Input: ";
    }

    protected static String messageFor(Throwable cause) {
        StringBuilder sb = new StringBuilder(getMessagePrefix());
        String name = cause.getClass().getSimpleName();
        if (name != null)
            sb.append('(').append(name).append(") ");
        sb.append(cause.getMessage());
        return sb.toString();
    }
}
