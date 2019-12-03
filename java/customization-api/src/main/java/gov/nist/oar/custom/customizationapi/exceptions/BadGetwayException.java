package gov.nist.oar.custom.customizationapi.exceptions;

public class BadGetwayException extends Exception {

    /**
     * Generated serial version UID
     */
    private static final long serialVersionUID = -5683479328564641953L;

    /**
     * Create an exception with an arbitrary message
     */
    public BadGetwayException(String msg) { super(msg); }

    /**
     * Create an exception with an arbitrary message and an underlying cause
     */
    public BadGetwayException(String msg, Throwable cause) { super(msg, cause); }

    /**
     * Create an exception with an underlying cause.  A default message is created.
     */
    public BadGetwayException(Throwable cause) { super(messageFor(cause), cause); }

    /**
     * return a message prefix that can introduce a more specific message
     */
    public static String getMessagePrefix() {
        return "Customization API exception encountered: ";
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
